import os
from datetime import datetime
from typing import Optional, List
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
