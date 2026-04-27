import os
import json
import time
import re
import argparse
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

# ─── Configuration ───────────────────────────────────────────────────────────

TARGET_URLS = [
    "https://www.linkedin.com/company/medical-dialogues/posts/",
    "https://www.linkedin.com/in/dr-shrey-bhatia-md/recent-activity/all/"
]

PAIN_POINT_KEYWORDS = [
    "clerical", "clerical work", "burden", "burnout", "exhausted", 
    "survey", "toxic", "mental health", "depression", "paperwork", 
    "admin work", "residency", "overworked", "stress"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# ─── Helper Functions ────────────────────────────────────────────────────────

def is_pain_point(text):
    """Check if the text contains formal medical community pain points."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in PAIN_POINT_KEYWORDS)

def format_lead(text, source_url):
    """Format a LinkedIn post/comment into the Supabase 'leads' schema."""
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    # Try to extract a user/company name from the URL
    user_id = "unknown"
    if "/company/" in source_url:
        user_id = source_url.split("/company/")[1].split("/")[0]
    elif "/in/" in source_url:
        user_id = source_url.split("/in/")[1].split("/")[0]

    return {
        "user_id": user_id,
        "pain_point": text.strip(),
        "email": None,
        "phone": None,
        "source": "linkedin",
        "created_at": now_str,
        "processed": False,
        "_meta": {
            "url": source_url
        }
    }

# ─── Main Logic ──────────────────────────────────────────────────────────────

def scrape_linkedin():
    print("\n⚠️ NOTE: LinkedIn aggressively blocks automated public scraping.")
    print("If you receive 429 (Too Many Requests) or 999 (Auth wall) errors,")
    print("you will need an authenticated approach (like Selenium or official APIs).\n")

    all_leads = []

    print(f"{'='*60}")
    print(f"🔗 PHASE 1: Scraping Target LinkedIn Pages")
    print(f"{'='*60}")

    for url in TARGET_URLS:
        print(f"  📥 Accessing: {url}...")
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code != 200:
                print(f"    ❌ Failed to fetch (Status: {response.status_code}). LinkedIn might be blocking the request.")
                time.sleep(3)
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            
            # LinkedIn's public post structure changes often.
            # We look for paragraphs or span tags that usually hold text.
            # (In a real scenario without Auth, LinkedIn often returns an Auth Wall page instead of posts).
            text_blocks = soup.find_all(['p', 'span', 'div'], class_=re.compile(r'(text|description|break-words)', re.I))
            
            count = 0
            # Deduplicate text blocks
            seen_texts = set()

            for block in text_blocks:
                text = block.get_text(separator=' ', strip=True)
                if len(text) < 40 or text in seen_texts:
                    continue
                    
                seen_texts.add(text)

                if is_pain_point(text):
                    lead = format_lead(text, url)
                    all_leads.append(lead)
                    count += 1

            print(f"    ✨ Found {count} potential pain points.")
            
        except Exception as e:
            print(f"    ❌ Error scraping {url}: {e}")
            
        time.sleep(5) # Respectful delay between profiles

    return all_leads

def save_results(leads):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "scraped_linkedin_leads.json")
    supabase_file = os.path.join(script_dir, "scraped_linkedin_leads_supabase_ready.json")

    # Full output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    # Supabase-ready (strip _meta)
    supabase_leads = []
    for lead in leads:
        clean = {k: v for k, v in lead.items() if k != "_meta"}
        supabase_leads.append(clean)

    with open(supabase_file, "w", encoding="utf-8") as f:
        json.dump(supabase_leads, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"📊 LINKEDIN SCRAPING SUMMARY")
    print(f"{'='*60}")
    print(f"  Total leads:           {len(leads)}")
    print(f"  💾 Full output:        {output_file}")
    print(f"  💾 Supabase-ready:     {supabase_file}")

if __name__ == "__main__":
    leads = scrape_linkedin()
    if leads:
        save_results(leads)
    else:
        print("\nNo leads found. LinkedIn likely served an Auth Wall (Login page).")
        print("To bypass this, you will need to use Browser Automation (like Selenium).")
