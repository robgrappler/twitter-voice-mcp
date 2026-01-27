import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from ai_handler import AIHandler
from data_handler import DataManager

def scan_and_draft(folder_path):
    load_dotenv()
    
    ai_handler = AIHandler()
    # Force the model to be sure
    ai_handler.model = "gemini-1.5-flash" 
    data_manager = DataManager()
    
    print(f"Scanning {folder_path}...")
    
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return

    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
    images = [
        f for f in os.listdir(folder_path) 
        if os.path.splitext(f)[1].lower() in valid_extensions
    ]
    
    if not images:
        print(f"No images found.")
        return
        
    for img_file in images:
        full_path = os.path.join(folder_path, img_file)
        print(f"Processing {img_file}...")
        
        # Generate 3 tweet options
        generated_tweets = ai_handler.generate_tweet_from_image(full_path, count=3)
        
        if generated_tweets and not generated_tweets[0].startswith("Error"):
            print(f"Generated {len(generated_tweets)} options:")
            for i, tweet_text in enumerate(generated_tweets):
                draft_id = data_manager.add_draft(
                    text=tweet_text,
                    media_path=full_path,
                    model=f"{ai_handler.provider}:{ai_handler.model}",
                    notes=f"Option {i+1} generated from image: {img_file}"
                )
                print(f"  [{i+1}] Draft {draft_id}: {tweet_text}")
        else:
            print(f"Failed: {generated_tweets[0] if generated_tweets else 'Unknown error'}")

if __name__ == "__main__":
    scan_and_draft("/Users/ppt04/Pictures/Twitter MCP/")
