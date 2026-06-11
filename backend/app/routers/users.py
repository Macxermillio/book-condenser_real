import os
import tempfile
import asyncio

from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.security import OAuth2PasswordRequestForm
from supabase import Client
from markdown_pdf import MarkdownPdf, Section

from app.db import get_supabase
from app.models import (
    SignUpMsg,
    UserCreate,
    User,
    PasswordResetRequest,
    PasswordReset,
    RefreshSessionRequest,
    LatestBookResponse,
)
from app.config import get_settings
from app.auth import get_current_user
from app.core.logging import logger
from app.services.extractor import extract_text
from app.services.llm import condense_with_llm
from app.utils.supabase_functions import supabase_func
from app.exceptions.auth import (
    UserAlreadyExistsError,
    SignupError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    PasswordResetError,
)
from app.exceptions.book import (
    RateLimitError,
    FileUploadError,
    FileDownloadError,
    TextExtractionError,
    LLMProcessingError,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Hmm

@router.post("/signup", response_model=SignUpMsg)
async def signup(
    user_data: UserCreate,
    supabase: Client = Depends(get_supabase),
):
    try:
        res = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {"data": {"full_name": user_data.full_name}},
        })
    except Exception as e:
        raise SignupError(
            log_message=f"Supabase signup error for {user_data.email}: {e}"
        ) from e

    if res.user.identities is not None and len(res.user.identities) == 0:
        raise UserAlreadyExistsError(
            log_message=f"Signup attempt for existing email: {user_data.email}"
        )

    if not res.user:
        raise SignupError(
            log_message=f"Supabase returned no user for {user_data.email}"
        )

    return {"message": "Signup successful"}


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    supabase: Client = Depends(get_supabase),
):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password,
        })
    except Exception as e:
        raise InvalidCredentialsError(
            log_message=f"Login failed for {form_data.username}: {e}"
        ) from e

    if not res.user.email_confirmed_at:
        raise EmailNotVerifiedError(
            log_message=f"Unverified email login attempt: {form_data.username}"
        )

    return {
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh_session(
    body: RefreshSessionRequest,
    supabase: Client = Depends(get_supabase),
):
    try:
        res = supabase.auth.refresh_session(body.refresh_token)
    except Exception as e:
        raise InvalidCredentialsError(
            log_message=f"Session refresh failed: {e}"
        ) from e

    if not res.session:
        raise InvalidCredentialsError(
            log_message="Supabase returned no session during refresh"
        )

    return {
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=User)
async def read_users_me(user: dict = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.user_metadata.get("full_name"),
        "created_at": user.created_at,
        "is_active": True,
    }


@router.post("/forgot-password")
async def forgot_password(
    body: PasswordResetRequest,
    supabase: Client = Depends(get_supabase),
):
    settings = get_settings()
    redirect_url = f"{settings.frontend_url}/reset-password"
    try:
        supabase.auth.reset_password_for_email(
            body.email,
            options={"redirect_to": redirect_url},
        )
    except Exception as e:
        raise PasswordResetError(
            log_message=f"Password reset request failed for {body.email}: {e}"
        ) from e
    return {
        "message": (
            "If that email is registered you will receive "
            "a password reset link shortly"
        )
    }


@router.post("/reset-password")
async def reset_password(
    body: PasswordReset,
    supabase: Client = Depends(get_supabase),
):
    try:
        supabase.auth.set_session(body.access_token, body.refresh_token)
        supabase.auth.update_user({"password": body.new_password})
    except Exception as e:
        raise PasswordResetError(
            log_message=f"Password reset failed: {e}"
        ) from e
    return {"message": "Password updated successfully"}


def _mark_book_error(book_id: str | None):
    if book_id:
        try:
            supabase_func.update_book(book_id, status="error")
        except Exception as e:
            logger.warning("Failed to mark book=%s as error: %s", book_id, e)


async def process_book_task(file: str, user_id: str, book_id: str | None = None):
    try:
        path = supabase_func.download_file(file, user_id)
    except Exception as e:
        supabase_func.log_deletion(user_id)
        _mark_book_error(book_id)
        raise FileDownloadError(
            log_message=(
                f"Download failed — user={user_id} file={file}: {e}"
            )
        ) from e

    try:
        full_text = extract_text(path)
        logger.info("Extracted %d characters from %s", len(full_text), path)
    except Exception as e:
        supabase_func.log_deletion(user_id)
        _mark_book_error(book_id)
        raise TextExtractionError(
            log_message=f"Extraction failed for {path}: {e}"
        ) from e

    try:
        result = await condense_with_llm(full_text)
        tokens_saved = result["tokens_in"] - result["tokens_out"]
        logger.info(
            "Condensation complete — user=%s tokens_saved=%d",
            user_id,
            tokens_saved,
        )
    except Exception as e:
        supabase_func.log_deletion(user_id)
        _mark_book_error(book_id)
        raise LLMProcessingError(
            log_message=f"LLM processing failed — user={user_id}: {e}"
        ) from e

    base_name = os.path.splitext(file)[0]
    filename = f"{base_name}_condensed.pdf"

    pdf_path = os.path.join(tempfile.gettempdir(), filename)
    pdf = MarkdownPdf(toc_level=0)
    pdf.add_section(Section(result["text"]))
    pdf.save(pdf_path)
    with open(pdf_path, "rb") as f:
        condensed_bytes = f.read()
    os.remove(pdf_path)

    try:
        upload_result = supabase_func.upload_file(
            condensed_bytes, filename, user_id, content_type="application/pdf"
        )
        if not upload_result:
            supabase_func.log_deletion(user_id)
            _mark_book_error(book_id)
            raise FileUploadError(
                log_message=(
                    f"Storage returned falsy for condensed upload "
                    f"— user={user_id} file={filename}"
                )
            )
    except FileUploadError:
        supabase_func.log_deletion(user_id)
        _mark_book_error(book_id)
        raise
    except Exception as e:
        supabase_func.log_deletion(user_id)
        _mark_book_error(book_id)
        raise FileUploadError(
            log_message=f"Condensed upload failed — user={user_id}: {e}"
        ) from e

    os.remove(path)
    download_url = supabase_func.create_download_url(filename, user_id)

    if book_id:
        try:
            supabase_func.update_book(
                book_id,
                status="done",
                condensed_filename=filename,
                download_url=download_url,
            )
        except Exception as e:
            logger.warning(
                "Failed to persist download for book=%s: %s", book_id, e
            )

    return download_url


async def schedule_deletion(file: str, user_id: str, delay: int = 1800):
    await asyncio.sleep(delay)
    try:
        supabase_func.delete_file(file, user_id)
    except Exception as e:
        logger.warning(
            "Scheduled deletion failed — file=%s user=%s: %s",
            file,
            user_id,
            e,
        )

async def delete_log(user_id: str, delay: int = 900):
    await asyncio.sleep(delay)
    try:
        supabase_func.log_deletion(user_id)
    except Exception as e:
        logger.warning(
            "Scheduled deletion log failed — user=%s: %s",
            user_id,
            e,
        )

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    if len(supabase_func.get_recent_usage(user.id)) > 0:
        raise RateLimitError(
            log_message=f"Rate limit exceeded for user={user.id}"
        )
    await asyncio.sleep(10)
    try:
        book_id = supabase_func.log_usage(
            user_id=user.id, file_name=file.filename, email=user.email
        )
        asyncio.create_task(delete_log(user.id))
    except Exception as e:

        logger.warning(
            "Failed to log usage for user=%s: %s",
            user.id,
            e,
        )

        raise RateLimitError(
            log_message=f"Rate limit exceeded for user={user.id}"
        ) from e

    file_bytes = await file.read()

    if not supabase_func.upload_file(file_bytes, file.filename, user.id):
        supabase_func.log_deletion(user.id)
        _mark_book_error(book_id)
        raise FileUploadError(
            log_message=(
                f"Initial upload returned falsy "
                f"— user={user.id} file={file.filename}"
            )
        )

    condensed_filename = (
        f"{os.path.splitext(file.filename)[0]}_condensed.pdf"
    )
    download_url = await process_book_task(
        file.filename, user.id, book_id=book_id
    )

    asyncio.create_task(schedule_deletion(file.filename, user.id))
    asyncio.create_task(schedule_deletion(condensed_filename, user.id))

    return {
        "message": "Your book is ready to download!",
        "download_url": download_url,
    }


def _book_download_url(book: dict, user_id: str) -> str | None:
    condensed_filename = book.get("condensed_filename")
    if book.get("status") != "done" or not condensed_filename:
        return None
    try:
        return supabase_func.create_download_url(condensed_filename, user_id)
    except Exception as e:
        logger.warning(
            "Failed to create download URL for book=%s: %s", book.get("id"), e
        )
        return book.get("download_url")


@router.get("/latest-book", response_model=LatestBookResponse)
async def latest_book(
    user=Depends(get_current_user),
    filename: str | None = Query(default=None),
):
    book = supabase_func.get_recoverable_book(user.id, original_filename=filename)
    if not book:
        return LatestBookResponse(status="none")

    return LatestBookResponse(
        id=book.get("id"),
        status=book.get("status", "unknown"),
        original_filename=book.get("original_filename"),
        download_url=_book_download_url(book, user.id),
        created_at=book.get("created_at"),
    )
