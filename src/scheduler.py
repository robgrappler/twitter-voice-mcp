import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
import pandas as pd
from data_handler import DataManager

class TweetScheduler:
    """Manages scheduled tweet posting via GitHub Actions or cron."""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.schedule_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "data", 
            "schedule.json"
        )
    
    def schedule_draft(self, draft_id: str, scheduled_time: str) -> bool:
        """
        Schedule a draft for posting at a specific time.
        Format: ISO 8601 (YYYY-MM-DDTHH:MM:SS)
        """
        try:
            # Validate ISO format
            datetime.fromisoformat(scheduled_time)
            
            df = pd.read_csv(self.data_manager.get_path_to_drafts_file(), keep_default_na=False)
            if draft_id not in df["id"].values:
                return False
            
            df.loc[df["id"] == draft_id, "scheduled_time"] = scheduled_time
            df.loc[df["id"] == draft_id, "status"] = "scheduled"
            df.to_csv(self.data_manager.get_path_to_drafts_file(), index=False)
            
            return True
        except Exception as e:
            print(f"Error scheduling draft: {e}")
            return False
    
    def get_due_posts(self) -> List[dict]:
        """
        Get all posts that are due to be posted now.
        Used by GitHub Actions or cron job.
        """
        try:
            df = pd.read_csv(self.data_manager.get_path_to_drafts_file(), keep_default_na=False)
            scheduled = df[df["status"] == "scheduled"]
            
            if scheduled.empty:
                return []
            
            now = datetime.now().isoformat()
            due = scheduled[scheduled["scheduled_time"] <= now]
            
            return due.to_dict("records")
        except Exception as e:
            print(f"Error getting due posts: {e}")
            return []
    
    def get_next_pending_draft(self) -> Optional[Dict]:
        """Fetch the oldest pending draft."""
        drafts = self.data_manager.list_pending_drafts()
        if not drafts:
            return None
        # drafts are returned as list of dicts, created_at is ISO string
        # They should be sorted by created_at naturally if appended to CSV
        return drafts[0]

    def is_strategy_slot(self, dt_utc: datetime) -> bool:
        """
        Check if the given UTC time matches a strategy slot.
        Vampire Mode (CST): Mon/Tue/Fri at 00:00, 01:00, 02:00
        Growth Mode (CST): Everyday at 08:00, 14:00
        CST is UTC-6.
        """
        # Convert UTC to CST (UTC-6)
        cst_time = dt_utc - timedelta(hours=6)
        
        hour = cst_time.hour
        minute = cst_time.minute
        weekday = cst_time.weekday() # 0 is Monday
        
        # Only check at the top of the hour (allowing for some drift, e.g., first 5 mins)
        if minute >= 5:
            return False
            
        # Growth Mode: Everyday at 08:00 and 14:00 CST
        if hour in [8, 14]:
            return True
            
        # Vampire Mode: Mon(0), Tue(1), Fri(4) at 00:00, 01:00, 02:00 CST
        if weekday in [0, 1, 4] and hour in [0, 1, 2]:
            return True
            
        return False
    
    def list_scheduled(self) -> List[dict]:
        """List all scheduled posts."""
        try:
            df = pd.read_csv(self.data_manager.get_path_to_drafts_file(), keep_default_na=False)
            scheduled = df[df["status"] == "scheduled"]
            return scheduled.to_dict("records")
        except Exception as e:
            print(f"Error listing scheduled: {e}")
            return []
    
    def unschedule_draft(self, draft_id: str) -> bool:
        """Unschedule a draft, returning it to pending status."""
        try:
            df = pd.read_csv(self.data_manager.get_path_to_drafts_file(), keep_default_na=False)
            if draft_id not in df["id"].values:
                return False
            
            df.loc[df["id"] == draft_id, "scheduled_time"] = ""
            df.loc[df["id"] == draft_id, "status"] = "pending"
            df.to_csv(self.data_manager.get_path_to_drafts_file(), index=False)
            
            return True
        except Exception as e:
            print(f"Error unscheduling draft: {e}")
            return False
