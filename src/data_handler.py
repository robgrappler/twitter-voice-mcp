import csv
import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict
import uuid

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DRAFTS_FILE = os.path.join(DATA_DIR, "drafts.csv")
POSTED_LOG = os.path.join(DATA_DIR, "posted_history.csv")

os.makedirs(DATA_DIR, exist_ok=True)

class DataManager:
    DRAFTS_HEADERS = [
        "id", "text", "media_path", "model_used", "status",
        "created_at", "scheduled_time", "notes", "is_retweet", "original_tweet_id"
    ]

    POSTED_HEADERS = [
        "id", "text", "media_path", "posted_at", "tweet_id"
    ]

    def __init__(self):
        self._init_csvs()

    def _init_csvs(self):
        if not os.path.exists(DRAFTS_FILE):
            with open(DRAFTS_FILE, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.DRAFTS_HEADERS)
                writer.writeheader()
        
        if not os.path.exists(POSTED_LOG):
             with open(POSTED_LOG, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.POSTED_HEADERS)
                writer.writeheader()

    def add_draft(self, text: str, media_path: str = None, model: str = "manual", 
                 notes: str = "", is_retweet: bool = False, original_tweet_id: str = None) -> str:
        if not os.path.exists(DRAFTS_FILE):
             self._init_csvs()

        draft_id = str(uuid.uuid4())[:8]
        new_row = {
            "id": draft_id,
            "text": text,
            "media_path": media_path if media_path else "",
            "model_used": model,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "scheduled_time": "",
            "notes": notes,
            "is_retweet": str(is_retweet), # Store as string "True"/"False" to match pandas behavior
            "original_tweet_id": original_tweet_id if original_tweet_id else ""
        }

        with open(DRAFTS_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.DRAFTS_HEADERS)
            writer.writerow(new_row)

        return draft_id

    def list_pending_drafts(self) -> List[Dict]:
        if not os.path.exists(DRAFTS_FILE):
            return []

        pending = []
        with open(DRAFTS_FILE, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["status"] == "pending":
                    # Convert boolean string to bool
                    row["is_retweet"] = (row.get("is_retweet") == "True")
                    pending.append(row)
        return pending

    def get_draft(self, draft_id: str) -> Optional[Dict]:
        if not os.path.exists(DRAFTS_FILE):
            return None

        with open(DRAFTS_FILE, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["id"] == draft_id:
                     row["is_retweet"] = (row.get("is_retweet") == "True")
                     return row
        return None

    def update_draft_status(self, draft_id: str, status: str):
        if not os.path.exists(DRAFTS_FILE):
            return

        rows = []
        updated = False
        fieldnames = []

        with open(DRAFTS_FILE, "r", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row["id"] == draft_id:
                    row["status"] = status
                    updated = True
                rows.append(row)

        if updated and fieldnames:
             with open(DRAFTS_FILE, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

    def mark_as_posted(self, draft_id: str, tweet_id: str):
        self.update_draft_status(draft_id, "posted")
        draft = self.get_draft(draft_id)
        
        if not draft:
            return

        # Prepare log entry
        new_log = {
            "id": draft_id,
            "text": draft["text"],
            "media_path": draft["media_path"],
            "posted_at": datetime.now().isoformat(),
            "tweet_id": tweet_id
        }

        if not os.path.exists(POSTED_LOG):
             self._init_csvs()

        with open(POSTED_LOG, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.POSTED_HEADERS)
            writer.writerow(new_log)

    def get_path_to_drafts_file(self) -> str:
        return DRAFTS_FILE
