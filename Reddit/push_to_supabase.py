import json
import os
import requests

# Supabase configuration (to be filled by user or from env vars)
# SUPABASE_URL = os.getenv("SUPABASE_URL", "your-project-url.supabase.co") #https://sdejjqadmrbmouupqakq.supabase.co
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://sdejjqadmrbmouupqakq.supabase.co")

SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-anon-key")

# Resolve paths relative to this script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILE = os.path.join(SCRIPT_DIR, "scraped_leads_supabase_ready.json")

def push_leads(file_path=DEFAULT_FILE):
    """Push leads from a JSON file to Supabase."""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        leads = json.load(f)

    if not leads:
        print("No leads to push.")
        return

    # Rewrite the source field to just be "reddit" as requested
    for lead in leads:
        lead["source"] = "reddit"

    print(f"Pushing {len(leads)} leads to Supabase...")

    # Supabase REST API endpoint for the 'leads' table
    url = f"{SUPABASE_URL}/rest/v1/leads"
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"  # Don't return the inserted rows
    }

    try:
        response = requests.post(url, headers=headers, json=leads)
        if response.status_code in [200, 201]:
            print("✅ Successfully pushed leads to Supabase.")
        else:
            print(f"❌ Failed to push leads: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error during push: {e}")

if __name__ == "__main__":
    if SUPABASE_KEY == "your-anon-key":
        print("⚠️ Please set SUPABASE_KEY environment variable first.")
        print("  export SUPABASE_KEY='your-anon-public-key'")
    else:
        push_leads()
