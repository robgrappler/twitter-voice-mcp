import os
import logging
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv
import json

load_dotenv()

consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

session = OAuth1Session(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=access_token,
    resource_owner_secret=access_token_secret,
)

username = "robgrappler"
user_url = f"https://api.twitter.com/2/users/by/username/{username}"

try:
    user_resp = session.get(user_url)
    if user_resp.status_code == 200:
        user_id = user_resp.json()["data"]["id"]
        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        params = {"max_results": 100, "exclude": "retweets,replies"}
        
        tweets_resp = session.get(tweets_url, params=params)
        if tweets_resp.status_code == 200:
            tweets = tweets_resp.json().get("data", [])
            print(f"Fetched {len(tweets)} tweets.")
            os.makedirs("data", exist_ok=True)
            with open("data/tweets.txt", "w") as f:
                for t in tweets:
                    f.write(t["text"].replace("\n", " ") + "\n")
            print("Saved to data/tweets.txt")
        else:
            print(f"Error fetching tweets: {tweets_resp.text}")
    else:
        print(f"Error fetching user: {user_resp.text}")

except Exception as e:
    print(f"Error: {e}")
