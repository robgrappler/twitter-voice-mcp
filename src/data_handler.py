import csv
import os
from datetime import datetime
from typing import List, Optional, Dict
import uuid

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
            with open(DRAFTS_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "id", "text", "media_path", "model_used", "status",
                    "created_at", "scheduled_time", "notes", "is_retweet", "original_tweet_id"
                ])
        
        if not os.path.exists(POSTED_LOG):
            with open(POSTED_LOG, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "id", "text", "media_path", "posted_at", "tweet_id"
                ])
        
        if not os.path.exists(POST_ATTEMPT_LOG):
            with open(POST_ATTEMPT_LOG, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "draft_id", "status", "tweet_id", "error", "text"
                ])

    def add_draft(self, text: str, media_path: str = None, model: str = "manual", 
                 notes: str = "", is_retweet: bool = False, original_tweet_id: str = None) -> str:
        draft_id = str(uuid.uuid4())[:8]
        row = [
            draft_id,
            text,
            media_path or "",
            model,
            "pending",
            datetime.now().isoformat(),
            "",  # scheduled_time
            notes,
            is_retweet,
            original_tweet_id or ""
        ]

        with open(DRAFTS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        return draft_id

    def list_pending_drafts(self) -> List[Dict]:
        pending = []
        if os.path.exists(DRAFTS_FILE):
            with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("status") == "pending":
                        pending.append(self._convert_row(row))
        return pending

    def get_draft(self, draft_id: str) -> Optional[Dict]:
        if os.path.exists(DRAFTS_FILE):
            with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("id") == draft_id:
                        return self._convert_row(row)
        return None

    def update_draft_status(self, draft_id: str, status: str):
        if not os.path.exists(DRAFTS_FILE):
            return

        rows = []
        updated = False
        fieldnames = []

        # Read all rows
        with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row.get("id") == draft_id:
                    row["status"] = status
                    updated = True
                rows.append(row)

        # Write back if updated
        if updated and fieldnames:
            with open(DRAFTS_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

    def mark_as_posted(self, draft_id: str, tweet_id: str, text: str = None, media_path: str = None):
        """
        Marks a draft as posted and logs it to history.
        Optimized to use O(1) append for logging instead of O(N) DataFrame rewrite.
        """
        self.update_draft_status(draft_id, "posted")
        
        if text is None or media_path is None:
            draft = self.get_draft(draft_id)
            if draft:
                text = draft.get("text", "")
                media_path = draft.get("media_path", "")
            else:
                text = ""
                media_path = ""

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

    def _convert_row(self, row: Dict) -> Dict:
        """Helper to convert string values from CSV to appropriate types."""
        # Convert is_retweet to boolean
        if "is_retweet" in row:
            val = row["is_retweet"]
            if isinstance(val, str):
                if val.lower() == "true":
                    row["is_retweet"] = True
                elif val.lower() == "false":
                    row["is_retweet"] = False
        return row

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

        if os.path.exists(DRAFTS_FILE):
            with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as f_in, \
                 open(safe_file, 'w', newline='', encoding='utf-8') as f_out:

                reader = csv.DictReader(f_in)
                fieldnames = reader.fieldnames
                writer = csv.DictWriter(f_out, fieldnames=fieldnames)
                writer.writeheader()

                for row in reader:
                    safe_row = {k: self._sanitize_csv_field(v) for k, v in row.items()}
                    writer.writerow(safe_row)

        return safe_file

    def get_path_to_drafts_file(self) -> str:
        return DRAFTS_FILE
