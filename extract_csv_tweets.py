
import csv
import os

csv_path = "/Volumes/Predator SSD/Predator Downloads/Robgrappler Tweets Jan 25 2026.csv"
output_path = "data/manual_tweets.txt"

os.makedirs("data", exist_ok=True)

try:
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        count = 0
        with open(output_path, "w", encoding="utf-8") as out:
            for row in reader:
                # Filter out pure retweets if possible
                # The 'type' column seems to distinguish them
                tweet_type = row.get("type", "").lower()
                text = row.get("text", "")
                
                # Check for RT @ at start just in case type is missing or different
                if tweet_type == "retweet" or text.startswith("RT @"):
                    continue
                    
                if text:
                    # Clean up newlines to keep one tweet per line for the tool
                    clean_text = text.replace("\n", " ").strip()
                    if clean_text:
                        out.write(clean_text + "\n")
                        count += 1
                        
    print(f"Extracted {count} tweets to {output_path}")

except Exception as e:
    print(f"Error: {e}")
