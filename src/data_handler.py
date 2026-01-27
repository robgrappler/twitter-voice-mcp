import pandas as pd
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
        df = pd.read_csv(DRAFTS_FILE, keep_default_na=False)
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
            "is_retweet": is_retweet,
            "original_tweet_id": original_tweet_id if original_tweet_id else ""
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DRAFTS_FILE, index=False)
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

    def mark_as_posted(self, draft_id: str, tweet_id: str):
        self.update_draft_status(draft_id, "posted")
        draft = self.get_draft(draft_id)
        
        log_df = pd.read_csv(POSTED_LOG, keep_default_na=False)
        new_log = {
            "id": draft_id,
            "text": draft["text"],
            "media_path": draft["media_path"],
            "posted_at": datetime.now().isoformat(),
            "tweet_id": tweet_id
        }
        log_df = pd.concat([log_df, pd.DataFrame([new_log])], ignore_index=True)
        log_df.to_csv(POSTED_LOG, index=False)

    def get_path_to_drafts_file(self) -> str:
        return DRAFTS_FILE
