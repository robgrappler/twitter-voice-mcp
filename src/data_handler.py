import pandas as pd
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
    def __init__(self):
        self._init_csvs()

    def _init_csvs(self):
        if not os.path.exists(DRAFTS_FILE):
            df = pd.DataFrame(columns=[
                "id", "text", "media_path", "model_used", "status", 
                "created_at", "scheduled_time", "notes", "is_retweet", "original_tweet_id"
            ])
            df.to_csv(DRAFTS_FILE, index=False)
        
        if not os.path.exists(POSTED_LOG):
            df = pd.DataFrame(columns=[
                "id", "text", "media_path", "posted_at", "tweet_id"
            ])
            df.to_csv(POSTED_LOG, index=False)

    def add_draft(self, text: str, media_path: str = None, model: str = "manual", 
                 notes: str = "", is_retweet: bool = False, original_tweet_id: str = None) -> str:
        draft_id = str(uuid.uuid4())[:8]

        # Prepare the row data preserving the column order defined in _init_csvs
        # ["id", "text", "media_path", "model_used", "status", "created_at", "scheduled_time", "notes", "is_retweet", "original_tweet_id"]
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
        df = pd.read_csv(DRAFTS_FILE, keep_default_na=False)
        pending = df[df["status"] == "pending"]
        return pending.to_dict("records")

    def get_draft(self, draft_id: str) -> Optional[Dict]:
        df = pd.read_csv(DRAFTS_FILE, keep_default_na=False)
        row = df[df["id"] == draft_id]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def update_draft_status(self, draft_id: str, status: str):
        df = pd.read_csv(DRAFTS_FILE, keep_default_na=False)
        if draft_id in df["id"].values:
            df.loc[df["id"] == draft_id, "status"] = status
            df.to_csv(DRAFTS_FILE, index=False)

    def mark_as_posted(self, draft_id: str, tweet_id: str, text: str = None, media_path: str = None):
        """
        Marks a draft as posted and logs it to history.
        Optimized to use O(1) append for logging instead of O(N) DataFrame rewrite.
        """
        self.update_draft_status(draft_id, "posted")
        
        # Use provided text/media_path if available to avoid reading file
        if text is None or media_path is None:
            draft = self.get_draft(draft_id)
            if draft:
                text = draft["text"]
                media_path = draft["media_path"]
            else:
                text = ""
                media_path = ""

        # Append to CSV directly (O(1)) instead of reading/writing with Pandas (O(N))
        # We assume the column order matches _init_csvs:
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

    def get_path_to_drafts_file(self) -> str:
        return DRAFTS_FILE

    def export_safe_drafts(self) -> str:
        """
        Export drafts to a new CSV file with sanitized fields to prevent CSV injection.
        """
        safe_file = os.path.join(DATA_DIR, "drafts_safe_export.csv")
        df = pd.read_csv(DRAFTS_FILE, keep_default_na=False)

        def sanitize(val):
            if isinstance(val, str) and val.startswith(('=', '+', '-', '@')):
                return "'" + val
            return val

        # Sanitize string columns that might contain user input
        for col in ["text", "notes", "media_path", "model_used"]:
             if col in df.columns:
                 df[col] = df[col].apply(sanitize)

        df.to_csv(safe_file, index=False)
        return safe_file
