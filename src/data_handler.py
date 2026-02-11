import csv
import os
from datetime import datetime
from typing import List, Optional, Dict
import uuid
import shutil
import tempfile

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DRAFTS_FILE = os.path.join(DATA_DIR, "drafts.csv")
POSTED_LOG = os.path.join(DATA_DIR, "posted_history.csv")
POST_ATTEMPT_LOG = os.path.join(DATA_DIR, "post_log.csv")

os.makedirs(DATA_DIR, exist_ok=True)

DRAFTS_FIELDS = [
    "id", "text", "media_path", "model_used", "status",
    "created_at", "scheduled_time", "notes", "is_retweet", "original_tweet_id"
]

POSTED_FIELDS = [
    "id", "text", "media_path", "posted_at", "tweet_id"
]

LOG_FIELDS = [
    "timestamp", "draft_id", "status", "tweet_id", "error", "text"
]

class DataManager:
    def __init__(self):
        self._init_csvs()

    def _init_csvs(self):
        if not os.path.exists(DRAFTS_FILE):
            with open(DRAFTS_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=DRAFTS_FIELDS)
                writer.writeheader()
        
        if not os.path.exists(POSTED_LOG):
            with open(POSTED_LOG, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=POSTED_FIELDS)
                writer.writeheader()
        
        if not os.path.exists(POST_ATTEMPT_LOG):
            with open(POST_ATTEMPT_LOG, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
                writer.writeheader()

    def add_draft(self, text: str, media_path: str = None, model: str = "manual", 
                 notes: str = "", is_retweet: bool = False, original_tweet_id: str = None) -> str:
        draft_id = str(uuid.uuid4())[:8]

        row = {
            "id": draft_id,
            "text": text,
            "media_path": media_path if media_path else "",
            "model_used": model,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "scheduled_time": "",
            "notes": notes,
            "is_retweet": str(is_retweet),
            "original_tweet_id": original_tweet_id if original_tweet_id else ""
        }

        needs_header = not os.path.exists(DRAFTS_FILE) or os.stat(DRAFTS_FILE).st_size == 0

        with open(DRAFTS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=DRAFTS_FIELDS)
            if needs_header:
                 writer.writeheader()
            writer.writerow(row)

        return draft_id

    def _process_row_types(self, row: Dict) -> Dict:
        """Helper to convert string CSV values to expected types (e.g. booleans)."""
        if 'is_retweet' in row:
            val = row['is_retweet']
            if val.lower() == 'true':
                row['is_retweet'] = True
            elif val.lower() == 'false':
                row['is_retweet'] = False
            # If neither, keep as is (or handle as False?)
        return row

    def list_pending_drafts(self) -> List[Dict]:
        """
        List all pending drafts using efficient CSV streaming.
        """
        pending = []
        if not os.path.exists(DRAFTS_FILE):
             return pending

        with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('status') == 'pending':
                    pending.append(self._process_row_types(row))
        return pending

    def get_draft(self, draft_id: str) -> Optional[Dict]:
        """
        Get a specific draft by ID using efficient CSV streaming.
        Stops reading once found.
        """
        if not os.path.exists(DRAFTS_FILE):
             return None

        with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('id') == draft_id:
                    return self._process_row_types(row)
        return None

    def update_draft_status(self, draft_id: str, status: str):
        """
        Update draft status efficiently without loading the entire file into memory.
        Uses streaming read/write to a temporary file.
        """
        if not os.path.exists(DRAFTS_FILE):
             return

        # Use safe temporary file creation
        temp_fd, temp_path = tempfile.mkstemp(dir=DATA_DIR, text=True)

        try:
            with os.fdopen(temp_fd, 'w', newline='', encoding='utf-8') as temp_file:
                with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as original_file:
                    reader = csv.DictReader(original_file)
                    # Preserve existing columns if possible, fallback to default
                    fieldnames = reader.fieldnames if reader.fieldnames else DRAFTS_FIELDS

                    writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
                    writer.writeheader()

                    for row in reader:
                        if row.get('id') == draft_id:
                            row['status'] = status
                        writer.writerow(row)

            # Atomic replace
            shutil.move(temp_path, DRAFTS_FILE)

        except Exception as e:
            # Clean up temp file if something goes wrong
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            raise e

    def mark_as_posted(self, draft_id: str, tweet_id: str, text: str = None, media_path: str = None):
        """
        Marks a draft as posted and logs it to history.
        Optimized to use streaming updates instead of full file load.
        """
        self.update_draft_status(draft_id, "posted")
        
        # Use provided text/media_path if available to avoid reading file again
        if text is None or media_path is None:
            draft = self.get_draft(draft_id)
            if draft:
                text = draft["text"]
                media_path = draft["media_path"]
            else:
                text = ""
                media_path = ""

        # Append to posted log
        row = {
            "id": draft_id,
            "text": text,
            "media_path": media_path,
            "posted_at": datetime.now().isoformat(),
            "tweet_id": tweet_id
        }

        needs_header = not os.path.exists(POSTED_LOG) or os.stat(POSTED_LOG).st_size == 0

        with open(POSTED_LOG, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=POSTED_FIELDS)
            if needs_header:
                writer.writeheader()
            writer.writerow(row)

    def log_attempt(self, status: str, draft_id: str = "", tweet_id: str = "", error: str = "", text: str = ""):
        """
        Logs a posting attempt (success or fail) to post_log.csv.
        """
        row = {
            "timestamp": datetime.now().isoformat(),
            "draft_id": draft_id,
            "status": status,
            "tweet_id": tweet_id,
            "error": error,
            "text": text[:50] + "..." if text and len(text) > 50 else text
        }
        
        needs_header = not os.path.exists(POST_ATTEMPT_LOG) or os.stat(POST_ATTEMPT_LOG).st_size == 0

        with open(POST_ATTEMPT_LOG, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
            if needs_header:
                 writer.writeheader()
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
        Updated to use streaming CSV processing instead of pandas.
        """
        safe_file = os.path.join(DATA_DIR, "drafts_safe_export.csv")

        if not os.path.exists(DRAFTS_FILE):
             with open(safe_file, 'w', newline='', encoding='utf-8') as f:
                 writer = csv.DictWriter(f, fieldnames=DRAFTS_FIELDS)
                 writer.writeheader()
             return safe_file

        with open(DRAFTS_FILE, 'r', newline='', encoding='utf-8') as infile, \
             open(safe_file, 'w', newline='', encoding='utf-8') as outfile:

            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames if reader.fieldnames else DRAFTS_FIELDS
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                safe_row = {k: self._sanitize_csv_field(v) for k, v in row.items()}
                writer.writerow(safe_row)

        return safe_file

    def get_path_to_drafts_file(self) -> str:
        return DRAFTS_FILE
