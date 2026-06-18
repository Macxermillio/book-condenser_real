import os
from datetime import datetime, timedelta, timezone

from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def main():
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    # ── Usage logs older than 1 hour ──────────────────────────────
    r = supabase.table("usage_logs").delete().lt("created_at", cutoff).execute()
    logs_cleaned = len(r.data)
    print(f"Deleted {logs_cleaned} usage log(s) older than 1 hour")

    # ── Books with status "done" or "error" older than 1 hour ────
    old_books = (
        supabase.table("books")
        .select("id, user_id, original_filename, condensed_filename")
        .lt("created_at", cutoff)
        .in_("status", ["done", "error"])
        .execute()
    )

    for book in old_books.data:
        user_id = book["user_id"]

        # Remove storage files
        for fname in [book["original_filename"], book.get("condensed_filename")]:
            if fname:
                path = f"{user_id}/{fname}"
                try:
                    supabase.storage.from_("books").remove([path])
                    print(f"  Deleted storage: {path}")
                except Exception as e:
                    # File may already be gone — that's fine
                    print(f"  Skipped storage {path}: {e}")

        # Remove DB record
        supabase.table("books").delete().eq("id", book["id"]).execute()
        print(f"  Deleted book record: {book['id']}")

    books_cleaned = len(old_books.data)
    print(f"Cleaned {books_cleaned} old book record(s)")


if __name__ == "__main__":
    main()
