import csv
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from typing import List, Optional, Dict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DRAFTS_FILE = os.path.join(DATA_DIR, "drafts.csv")
POSTED_LOG = os.path.join(DATA_DIR, "posted_history.csv")
POST_ATTEMPT_LOG = os.path.join(DATA_DIR, "post_log.csv")

os.makedirs(DATA_DIR, exist_ok=True)

class DataManager:
    def __init__(self):
        self._init_csvs()

    def _init_csvs(self):
        if not os.path.exists(DRAFTS_FILE):
            headers = [
                "id", "text", "media_path", "model_used", "status", 
                "created_at", "scheduled_time", "notes", "is_retweet", "original_tweet_id"
            ]
            with open(DRAFTS_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        
        if not os.path.exists(POSTED_LOG):
            headers = ["id", "text", "media_path", "posted_at", "tweet_id"]
            with open(POSTED_LOG, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        
        if not os.path.exists(POST_ATTEMPT_LOG):
            headers = ["timestamp", "draft_id", "status", "tweet_id", "error", "text"]
            with open(POST_ATTEMPT_LOG, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def add_draft(self, text: str, media_path: str = None, model: str = "manual", 
                 notes: str = "", is_retweet: bool = False, original_tweet_id: str = None) -> str:
        draft_id = str(uuid.uuid4())[:8]

        # Prepare the row data preserving the column order defined in _init_csvs
        row = [
            draft_id,
            text,
            media_path if media_path else "",
            model,
            "pending",
            datetime.now().isoformat(),
            "",  # scheduled_time
            notes,
            is_retweet,
            original_tweet_id if original_tweet_id else ""
        ]

        with open(DRAFTS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        return draft_id

    def list_pending_drafts(self) -> List[Dict]:
        if not os.path.exists(DRAFTS_FILE):
            return []

        pending = []
        with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status") == "pending":
                    pending.append(row)
        return pending

    def get_first_pending_draft(self) -> Optional[Dict]:
        """
        Stream the CSV file and return the first pending draft found.
        This is O(k) memory and speed, where k is the index of the first pending draft.
        Avoids reading the entire file into memory (O(N)) when only one is needed.
        """
        if not os.path.exists(DRAFTS_FILE):
            return None

        with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status") == "pending":
                    return row
        return None

    def get_draft(self, draft_id: str) -> Optional[Dict]:
        if not os.path.exists(DRAFTS_FILE):
            return None

        with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("id") == draft_id:
                    return row
        return None

    def update_draft_status(self, draft_id: str, status: str):
        if not os.path.exists(DRAFTS_FILE):
            return

        # Atomic update using temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', newline='', encoding='utf-8', delete=False, dir=DATA_DIR)
        updated = False

        try:
            with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as f_in, temp_file as f_out:
                reader = csv.DictReader(f_in)
                writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
                writer.writeheader()

                for row in reader:
                    if row.get("id") == draft_id:
                        row["status"] = status
                        updated = True
                    writer.writerow(row)

            if updated:
                shutil.move(temp_file.name, DRAFTS_FILE)
            else:
                os.unlink(temp_file.name)

        except Exception as e:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise e

    def mark_as_posted(self, draft_id: str, tweet_id: str, text: str = None, media_path: str = None):
        """
        Marks a draft as posted and logs it to history.
        Optimized to use O(1) append for logging instead of O(N) DataFrame rewrite.
        """
        # Optimize: If we have text/media_path, we don't need to read the file to log it.
        # But we still need to update status.
        # Since update_draft_status reads the file anyway, maybe we can combine them?
        # For now, let's stick to update_draft_status + logging.

        self.update_draft_status(draft_id, "posted")
        
        # Use provided text/media_path if available to avoid reading file
        if text is None or media_path is None:
            draft = self.get_draft(draft_id)
            if draft:
                text = draft.get("text", "")
                media_path = draft.get("media_path", "")
            else:
                text = ""
                media_path = ""

        # Append to CSV directly (O(1))
        # ["id", "text", "media_path", "posted_at", "tweet_id"]
        row = [
            draft_id,
            text,
            media_path,
            datetime.now().isoformat(),
            tweet_id
        ]

        with open(POSTED_LOG, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def log_attempt(self, status: str, draft_id: str = "", tweet_id: str = "", error: str = "", text: str = ""):
        """
        Logs a posting attempt (success or fail) to post_log.csv.
        """
        row = [
            datetime.now().isoformat(),
            draft_id,
            status,
            tweet_id,
            error,
            text[:50] + "..." if text and len(text) > 50 else text
        ]
        
        with open(POST_ATTEMPT_LOG, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def _sanitize_csv_field(self, field: any) -> any:
        """
        Sanitize a field for CSV injection (Excel formula injection).
        If a field is a string and starts with =, +, -, or @, prepend a single quote.
        """
        if isinstance(field, str) and field and field[0] in ('=', '+', '-', '@'):
            return f"'{field}"
        return field

    def export_safe_drafts(self) -> str:
        """
        Creates a sanitized copy of the drafts CSV for manual review.
        Prevents CSV formula injection.
        """
        safe_file = os.path.join(DATA_DIR, "drafts_safe_export.csv")

        if not os.path.exists(DRAFTS_FILE):
             # If no file, just create empty export
             with open(safe_file, 'w', newline='', encoding='utf-8') as f:
                 pass # Or headers? Let's assume headers are needed if possible but DictReader handles reading.
                 # If original doesn't exist, we can't read fieldnames.
             return safe_file

        with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as f_in, \
             open(safe_file, 'w', newline='', encoding='utf-8') as f_out:

            reader = csv.DictReader(f_in)
            writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
            writer.writeheader()

            for row in reader:
                safe_row = {k: self._sanitize_csv_field(v) for k, v in row.items()}
                writer.writerow(safe_row)

        return safe_file

    def get_path_to_drafts_file(self) -> str:
        return DRAFTS_FILE
