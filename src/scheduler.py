import os
import csv
import shutil
import tempfile
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from data_handler import DataManager

class TweetScheduler:
    """Manages scheduled tweet posting via GitHub Actions or cron."""
    
    def __init__(self):
        self.data_manager = DataManager()
        # schedule.json is legacy/unused, ignoring as per original code behavior (which ignored it in favor of drafts.csv)
    
    def schedule_draft(self, draft_id: str, scheduled_time: str) -> bool:
        """
        Schedule a draft for posting at a specific time.
        Format: ISO 8601 (YYYY-MM-DDTHH:MM:SS)
        """
        drafts_file = self.data_manager.get_path_to_drafts_file()
        if not os.path.exists(drafts_file):
            return False

        try:
            # Validate ISO format
            datetime.fromisoformat(scheduled_time)
            
            updated = False
            temp_file = tempfile.NamedTemporaryFile(mode='w', newline='', encoding='utf-8', delete=False, dir=os.path.dirname(drafts_file))
            
            try:
                with open(drafts_file, 'r', newline='', encoding='utf-8') as f_in, temp_file:
                    reader = csv.DictReader(f_in)
                    fieldnames = reader.fieldnames
                    writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
                    writer.writeheader()

                    found = False
                    for row in reader:
                        if row.get("id") == draft_id:
                            row["scheduled_time"] = scheduled_time
                            row["status"] = "scheduled"
                            found = True
                            updated = True
                        writer.writerow(row)

                if updated:
                    shutil.move(temp_file.name, drafts_file)
                    return True
                else:
                    os.unlink(temp_file.name)
                    return False

            except Exception as e:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                raise e

        except Exception as e:
            print(f"Error scheduling draft: {e}")
            return False
    
    def get_due_posts(self) -> List[dict]:
        """
        Get all posts that are due to be posted now.
        Used by GitHub Actions or cron job.
        """
        drafts_file = self.data_manager.get_path_to_drafts_file()
        if not os.path.exists(drafts_file):
            return []

        try:
            due_posts = []
            now = datetime.now().isoformat()
            
            with open(drafts_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("status") == "scheduled":
                        scheduled_time = row.get("scheduled_time")
                        if scheduled_time and scheduled_time <= now:
                            due_posts.append(self.data_manager.process_row(row))

            return due_posts
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
        drafts_file = self.data_manager.get_path_to_drafts_file()
        if not os.path.exists(drafts_file):
            return []

        try:
            scheduled = []
            with open(drafts_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("status") == "scheduled":
                        scheduled.append(self.data_manager.process_row(row))
            return scheduled
        except Exception as e:
            print(f"Error listing scheduled: {e}")
            return []
    
    def unschedule_draft(self, draft_id: str) -> bool:
        """Unschedule a draft, returning it to pending status."""
        drafts_file = self.data_manager.get_path_to_drafts_file()
        if not os.path.exists(drafts_file):
            return False
            
        try:
            updated = False
            temp_file = tempfile.NamedTemporaryFile(mode='w', newline='', encoding='utf-8', delete=False, dir=os.path.dirname(drafts_file))
            
            try:
                with open(drafts_file, 'r', newline='', encoding='utf-8') as f_in, temp_file:
                    reader = csv.DictReader(f_in)
                    fieldnames = reader.fieldnames
                    writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
                    writer.writeheader()

                    found = False
                    for row in reader:
                        if row.get("id") == draft_id:
                            row["scheduled_time"] = ""
                            row["status"] = "pending"
                            found = True
                            updated = True
                        writer.writerow(row)

                if updated:
                    shutil.move(temp_file.name, drafts_file)
                    return True
                else:
                    os.unlink(temp_file.name)
                    return False

            except Exception as e:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                raise e

        except Exception as e:
            print(f"Error unscheduling draft: {e}")
            return False
