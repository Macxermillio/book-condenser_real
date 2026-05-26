from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.routers import users
from app.core.logging import logger
from app.exceptions.base import AppException
from app.exceptions.auth import AuthenticationError

app = FastAPI(
    title="Book Condenser API",
    description="API for condensing manuscripts with AI",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://book-condenser-real.vercel.app/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    if not token:
        raise AuthenticationError(
            log_message="Empty bearer token on /protected"
        )
    return token


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(exc.log_message)
    headers = {}
    if isinstance(exc, AuthenticationError):
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_type": exc.__class__.__name__,
        },
        headers=headers,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled application exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"},
    )


app.include_router(users.router)


@app.get("/protected")
def protected_route(token: str = Depends(verify_token)):
    return {"message": "You are authorized", "token": token}


@app.get("/")
def read_root():
    return {"message": "Book Condenser API is live! 📚✨"}
