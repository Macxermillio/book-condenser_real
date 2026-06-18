import os
from datetime import datetime, timedelta, timezone

from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def main():
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    r = supabase.table("usage_logs").delete().lt("created_at", cutoff).execute()
    print(f"Deleted {len(r.data)} usage log(s) older than 1 hour")

    old_books = (
        supabase.table("books")
        .select("id, user_id, original_filename, condensed_filename")
        .lt("created_at", cutoff)
        .in_("status", ["done", "error"])
        .execute()
    )

    for book in old_books.data:
        uid = book["user_id"]
        for fname in [book["original_filename"], book.get("condensed_filename")]:
            if fname:
                path = f"{uid}/{fname}"
                try:
                    supabase.storage.from_("books").remove([path])
                    print(f"  Deleted storage: {path}")
                except Exception as e:
                    # File may already be gone — not an error
                    print(f"  Skipped storage {path}: {e}")

    print(f"Cleaned storage files for {len(old_books.data)} old book(s)")
    print("(book DB records preserved)")


if __name__ == "__main__":
    main()