#!/usr/bin/env python3
"""
Scheduled tweet posting script for GitHub Actions.
Fetches all due scheduled tweets and posts them to Twitter.
"""

import sys
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from scheduler import TweetScheduler
from twitter_handler import TwitterHandler
from data_handler import DataManager


def _missing_twitter_credentials() -> list[str]:
    required = [
        "TWITTER_CONSUMER_KEY",
        "TWITTER_CONSUMER_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN_SECRET",
    ]
    return [key for key in required if not os.getenv(key)]

def main():
    load_dotenv()
    try:
        missing_keys = _missing_twitter_credentials()
        if missing_keys:
            print(
                f"[{datetime.now().isoformat()}] "
                f"Missing Twitter credentials: {', '.join(missing_keys)}. "
                "Skipping scheduled posting."
            )
            return 0

        scheduler = TweetScheduler()
        twitter = TwitterHandler()
        data_manager = DataManager()
        
        # Get all tweets due for posting
        due_posts = scheduler.get_due_posts()
        
        # Check if current time is a strategy slot
        now_utc = datetime.now(timezone.utc)
        if scheduler.is_strategy_slot(now_utc):
            print(f"[{now_utc.isoformat()}] Current time is a strategy slot. Checking for pending drafts...")
            next_draft = scheduler.get_next_pending_draft()
            if next_draft:
                print(f"  Found pending draft [{next_draft['id']}]. Adding to processing list.")
                # Avoid duplicates if it was already manually scheduled (unlikely but safe)
                if not any(p['id'] == next_draft['id'] for p in due_posts):
                    due_posts.append(next_draft)
            else:
                print("  No pending drafts found for this strategy slot.")
        
        if not due_posts:
            print(f"[{datetime.now().isoformat()}] No posts due or slots active.")
            return 0
        
        print(f"[{datetime.now().isoformat()}] Processing {len(due_posts)} posts.")
        
        posted_count = 0
        failed_count = 0
        
        for post in due_posts:
            draft_id = post["id"]
            text = post["text"]
            media_path = post["media_path"]
            
            try:
                print(f"  Posting [{draft_id}]...")
                
                # Post to Twitter
                result = twitter.post_tweet(text, media_path if media_path else None)
                
                if "error" in result:
                    error_msg = result['error']
                    print(f"    ERROR: {error_msg}")
                    data_manager.log_attempt("failed", draft_id=draft_id, error=error_msg, text=text)
                    failed_count += 1
                    continue
                
                tweet_id = result.get("data", {}).get("id")
                data_manager.mark_as_posted(draft_id, tweet_id, text, media_path)
                data_manager.log_attempt("success", draft_id=draft_id, tweet_id=tweet_id, text=text)
                print(f"    SUCCESS: Posted as tweet {tweet_id}")
                posted_count += 1
                
            except Exception as e:
                error_msg = str(e)
                print(f"    ERROR: {error_msg}")
                data_manager.log_attempt("error", draft_id=draft_id, error=error_msg, text=text)
                failed_count += 1
        
        print(f"[{datetime.now().isoformat()}] Posted {posted_count}, Failed {failed_count}")
        
        # Exit with error if any failed
        return 1 if failed_count > 0 else 0
        
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Fatal error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
