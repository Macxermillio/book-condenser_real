import os
import tempfile
from supabase import create_client
from app.config import get_settings
from datetime import datetime, timedelta, timezone
from app.core.logging import logger

_settings = get_settings()

supabase = create_client(_settings.supabase_url, _settings.supabase_service_key)



class supabase_func:

    @staticmethod
    def upload_file(file_bytes: bytes, filename: str, user_id: str, content_type: str = "application/octet-stream"):
        response = (
            supabase.storage
            .from_("books")
            .upload(
                file=file_bytes,
                path=f"{user_id}/{filename}",
                file_options={"cache-control": "3600", "upsert": "true", "content-type": content_type}
            )
        )
        return response

    @staticmethod
    def update_file(file_name: str, user_id: str):
        file_path = f"{user_id}/{file_name}"
        with open(file_path, "rb") as f:
            response = (
                supabase.storage
                .from_("books")
                .update(
                    file=f,
                    path=file_path,
                    file_options={"cache-control": "3600", "upsert": "true"}
                )
            )
        return response

    @staticmethod
    def create_download_url(file_name: str, user_id: str, expires_in: int = 3600):
        file_path = f"{user_id}/{file_name}"
        response = (
            supabase.storage
            .from_("books")
            .create_signed_url(
                file_path,
                expires_in,
                {"download": True},
            )
        )
        return response["signedURL"]

    @staticmethod
    def delete_file(file_name: str, user_id: str):
        file_path = f"{user_id}/{file_name}"
        response = (
            supabase.storage
            .from_("books")
            .remove([file_path])
        )
        return print(f"File {file_name} deleted from storage") if response else print(f"File {file_name} not found in storage")

    @staticmethod
    def download_file(file_name: str, user_id: str):
        local_path = os.path.join(tempfile.gettempdir(), file_name)
        file_path = f"{user_id}/{file_name}"
        with open(local_path, "wb+") as f:
            response = (
                supabase.storage
                .from_("books")
                .download(file_path)
            )
            f.write(response)
        return local_path

    @staticmethod
    def log_usage(user_id: str, tokens_in: int = 0, tokens_out: int = 0, cost_credits: float = 0.0, file_name: str = "unknown", email: str = "unknown"):

        (
            supabase.table("usage_logs")
            .insert({"user_id": user_id, "tokens_in": tokens_in, "tokens_out": tokens_out, "cost_credits": cost_credits})
            .execute()
        )

        add_book = (
            supabase.table("books")
            .insert({
                "user_id": user_id,
                "original_filename": file_name,
                "email": email,
                "status": "processing",
            })
            .select("id")
            .execute()
        )

        book_id = add_book.data[0]["id"] if add_book.data else None

        logger.info("Added book id=%s filename=%s", book_id, file_name)

        logger.info("Usage logged for user=%s", user_id)

        return book_id

    @staticmethod
    def update_book(
        book_id: str,
        *,
        status: str,
        condensed_filename: str | None = None,
        download_url: str | None = None,
    ):
        payload: dict = {"status": status}
        if condensed_filename is not None:
            payload["condensed_filename"] = condensed_filename
        if download_url is not None:
            payload["download_url"] = download_url

        response = (
            supabase.table("books")
            .update(payload)
            .eq("id", book_id)
            .execute()
        )
        return response.data[0] if response.data else None

    @staticmethod
    def get_recoverable_book(user_id: str, original_filename: str | None = None):
        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=60)

        query = (
            supabase.table("books")
            .select("*")
            .eq("user_id", user_id)
            .gte("created_at", time_threshold.isoformat())
            .order("created_at", desc=True)
        )
        if original_filename:
            query = query.eq("original_filename", original_filename)

        response = query.limit(1).execute()
        if not response.data:
            return None
        return response.data[0]

    @staticmethod
    def get_recent_usage(user_id: str):

        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=15)

        try:
            response = (
                supabase.table("usage_logs")
                .select("*")
                .eq("user_id", user_id)
                .gte("created_at", time_threshold.isoformat())
                .execute()
            )

            if len(response.data) > 0:
                logger.info("Recent usage found for user=%s", user_id)
            else:
                supabase_func.log_deletion(user_id=user_id)
            return response.data

        except Exception as e:
            print(f"Error retrieving logs: {e}")
            return []

    @staticmethod
    def log_deletion(user_id: str):

        try:
            response = (
                supabase.table("usage_logs")
                .delete()
                .eq("user_id", user_id)
                .execute()
            )


            if response.data and len(response.data) > 0:
                logger.info("Uplifted rate limit on user=%s", user_id)
                return True
            else:
                logger.warning(
                    "No usage logs found to delete for user=%s", user_id
                )
                return False

        except Exception as e:

            logger.error(
                "Database error while deleting logs for user=%s: %s", user_id, e
            )
            return False

