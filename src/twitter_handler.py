import os
import requests
from requests_oauthlib import OAuth1Session
import json
import logging
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
        Uploads media using v1.1 API and returns media_id.
        """
        if not self.session:
            raise Exception("Twitter credentials not configured")
            
        url = "https://upload.twitter.com/1.1/media/upload.json"
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Media file not found: {file_path}")
            
        try:
            with open(file_path, 'rb') as f:
                files = {'media': f}
                response = self.session.post(url, files=files)
                
            if response.status_code == 200:
                media_id = response.json().get('media_id_string')
                return media_id
            else:
                logger.error(f"Media upload failed: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error uploading media: {str(e)}")
            return None

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
