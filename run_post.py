import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Load env vars first
load_dotenv()

# Import the function and the initialized handlers from server
from server import approve_and_post_draft

if __name__ == "__main__":
    draft_id = "020382c6"
    print(f"Attempting to post draft {draft_id}...")
    result = approve_and_post_draft(draft_id)
    print(result)
