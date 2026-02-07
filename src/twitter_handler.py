import os
import requests
from requests_oauthlib import OAuth1Session
import json
import logging
import time
import tempfile
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class TwitterHandler:
    def __init__(self):
        self.consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
        self.consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
        # Cache for authenticated user ID (avoid repeated /users/me calls)
        self.user_id = None
        # Cache for username -> user_id lookups
        self.username_cache = {}
        self.session = None
        if self.consumer_key and self.access_token:
            self.session = OAuth1Session(
                self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=self.access_token,
                resource_owner_secret=self.access_token_secret,
            )

    def verify_credentials(self) -> bool:
        if not self.session:
            return False
        # v2 'me' endpoint
        url = "https://api.twitter.com/2/users/me"
        response = self.session.get(url)
        if response.status_code == 200:
            # Cache user_id from the response
            data = response.json().get("data", {})
            if "id" in data:
                self.user_id = data["id"]
            return True
        return False

    def upload_media(self, file_path: str) -> Optional[str]:
        """
        Uploads media using v1.1 API (chunked) and returns media_id.
        Supports both local paths and URLs.
        """
        if not self.session:
            raise Exception("Twitter credentials not configured")
            
        temp_file = None
        try:
            # Handle URL
            if file_path.startswith(('http://', 'https://')):
                logger.info(f"Downloading media from URL: {file_path}")
                response = requests.get(file_path, stream=True)
                if response.status_code != 200:
                    logger.error(f"Failed to download media: {response.text}")
                    return None
                
                # Use a specific extension if possible
                ext = os.path.splitext(file_path)[1].split('?')[0]
                if not ext: ext = ".tmp"
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file.close()
                file_path = temp_file.name

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Media file not found: {file_path}")
            
            # Use chunked upload for all files (reliable for large images/videos)
            return self._chunked_upload(file_path)
            
        except Exception as e:
            logger.error(f"Error uploading media: {str(e)}")
            return None
        finally:
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

    def _chunked_upload(self, file_path: str) -> Optional[str]:
        """
        Performs a chunked media upload (v1.1).
        """
        url = "https://upload.twitter.com/1.1/media/upload.json"
        
        file_size = os.path.getsize(file_path)
        # Determine media type
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.mp4', '.mov']: media_type = 'video/mp4'
        elif ext == '.gif': media_type = 'image/gif'
        else: media_type = 'image/jpeg' # Default
        
        # 1. INIT
        params = {
            "command": "INIT",
            "total_bytes": file_size,
            "media_type": media_type,
        }
        resp = self.session.post(url, data=params)
        if resp.status_code != 202:
            logger.error(f"INIT failed: {resp.text}")
            return None
        
        media_id = resp.json().get('media_id_string')
        
        # 2. APPEND
        segment_id = 0
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(1024 * 1024 * 4) # 4MB chunks
                if not chunk:
                    break
                
                params = {
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": segment_id
                }
                files = {"media": chunk}
                resp = self.session.post(url, data=params, files=files)
                if resp.status_code < 200 or resp.status_code > 299:
                    logger.error(f"APPEND failed segment {segment_id}: {resp.text}")
                    return None
                segment_id += 1
                
        # 3. FINALIZE
        params = {
            "command": "FINALIZE",
            "media_id": media_id
        }
        resp = self.session.post(url, data=params)
        if resp.status_code != 200:
            logger.error(f"FINALIZE failed: {resp.text}")
            return None
            
        # 4. STATUS (Optional but recommended for video)
        if media_type.startswith('video'):
            check_url = url
            while True:
                params = {
                    "command": "STATUS",
                    "media_id": media_id
                }
                resp = self.session.get(check_url, params=params)
                if resp.status_code != 200:
                    logger.error(f"STATUS check failed: {resp.text}")
                    return None
                
                status_data = resp.json()
                state = status_data.get('processing_info', {}).get('state')
                if state == 'succeeded':
                    break
                if state == 'failed':
                    logger.error(f"Media processing failed: {status_data}")
                    return None
                
                wait = status_data.get('processing_info', {}).get('check_after_secs', 5)
                time.sleep(wait)
                
        return media_id

    def post_tweet(self, text: str, media_path: str = None, reply_to_id: str = None) -> Dict:
        """
        Post tweet using v2 API.
        """
        if not self.session:
            raise Exception("Twitter credentials not configured")
            
        url = "https://api.twitter.com/2/tweets"
        payload = {"text": text}
        
        if media_path:
            media_id = self.upload_media(media_path)
            if media_id:
                payload["media"] = {"media_ids": [media_id]}
                
        if reply_to_id:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}
            
        try:
            response = self.session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            return {"error": str(e)}

    def get_user_tweets(self, username: str, count: int = 10) -> List[str]:
        """
        Fetch tweets from a user. 
        Note: Requires Basic Tier or higher for v2 user timeline.
        If Free Tier, this might fail.
        """
        # Check cache first
        if username in self.username_cache:
            user_id = self.username_cache[username]
        else:
            # First get user ID
            user_url = f"https://api.twitter.com/2/users/by/username/{username}"
            user_resp = self.session.get(user_url)
            
            if user_resp.status_code != 200:
                logger.error(f"Failed to get user ID: {user_resp.text}")
                return []
                
            data = user_resp.json().get("data")
            if not data:
                logger.error(f"No user data in response: {user_resp.text}")
                return []
            
            user_id = data.get("id")
            if not user_id:
                logger.error(f"No user ID in data: {data}")
                return []
            
            # Cache it
            self.username_cache[username] = user_id
        
        # Get tweets
        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        params = {"max_results": min(count, 100), "exclude": "retweets,replies"}
        
        tweets_resp = self.session.get(tweets_url, params=params)
        
        if tweets_resp.status_code == 200:
            data = tweets_resp.json().get("data", [])
            return [t["text"] for t in data]
        else:
            logger.error(f"Failed to get tweets: {tweets_resp.text}")
            return []

    def search_tweets(self, query: str, count: int = 10) -> List[Dict]:
        """
        Search tweets (Requires Basic Tier).
        """
        url = "https://api.twitter.com/2/tweets/search/recent"
        params = {
            "query": query,
            "max_results": min(count, 100),
            "tweet.fields": "author_id,created_at,public_metrics"
        }
        
        resp = self.session.get(url, params=params)
        
        if resp.status_code == 200:
            return resp.json().get("data", [])
        else:
            logger.error(f"Search failed: {resp.text}")
            return []

    def retweet(self, tweet_id: str) -> Dict:
        """
        Retweet a tweet.
        """
        # Use cached user_id if available
        if not self.user_id:
            me_resp = self.session.get("https://api.twitter.com/2/users/me")
            if me_resp.status_code != 200:
                return {"error": "Failed to get my user ID"}
            self.user_id = me_resp.json()["data"]["id"]
            
        my_id = self.user_id
        
        url = f"https://api.twitter.com/2/users/{my_id}/retweets"
        payload = {"tweet_id": tweet_id}
        
        resp = self.session.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": resp.text}
