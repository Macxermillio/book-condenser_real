import os
import tempfile
from supabase import create_client
from app.config import get_settings
from datetime import datetime, timedelta, timezone

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
    def create_download_url(file_name: str, user_id: str, expires_in: int = 1800):
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
    def log_usage(user_id: str, tokens_in: int = 0, tokens_out: int = 0, cost_credits: float = 0.0):

        response = (
            supabase.table("usage_logs")
            .insert({"user_id": user_id, "tokens_in": tokens_in, "tokens_out": tokens_out, "cost_credits": cost_credits})
            .execute()
        )

        return response

    @staticmethod
    def get_recent_usage(user_id: str):

        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=60)

        try:
            response = (
                supabase.table("usage_logs")
                .select("*")
                .eq("user_id", user_id)
                .gte("created_at", time_threshold.isoformat())
                .execute()
            )

            return response.data

        except Exception as e:
            print(f"Error retrieving logs: {e}")
            return []
