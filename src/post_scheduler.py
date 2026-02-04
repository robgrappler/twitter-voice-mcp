#!/usr/bin/env python3
"""
Scheduled tweet posting script for GitHub Actions.
Fetches all due scheduled tweets and posts them to Twitter.
"""

import sys
import os
from dotenv import load_dotenv
from datetime import datetime
from scheduler import TweetScheduler
from twitter_handler import TwitterHandler
from data_handler import DataManager

def main():
    load_dotenv()
    try:
        scheduler = TweetScheduler()
        twitter = TwitterHandler()
        data_manager = DataManager()
        
        # Get all tweets due for posting
        due_posts = scheduler.get_due_posts()
        
        if not due_posts:
            print(f"[{datetime.now().isoformat()}] No posts due at this time.")
            return 0
        
        print(f"[{datetime.now().isoformat()}] Found {len(due_posts)} posts due for posting.")
        
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
                    print(f"    ERROR: {result['error']}")
                    failed_count += 1
                    continue
                
                tweet_id = result.get("data", {}).get("id")
                data_manager.mark_as_posted(draft_id, tweet_id, text, media_path)
                print(f"    SUCCESS: Posted as tweet {tweet_id}")
                posted_count += 1
                
            except Exception as e:
                print(f"    ERROR: {str(e)}")
                failed_count += 1
        
        print(f"[{datetime.now().isoformat()}] Posted {posted_count}, Failed {failed_count}")
        
        # Exit with error if any failed
        return 1 if failed_count > 0 else 0
        
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Fatal error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
