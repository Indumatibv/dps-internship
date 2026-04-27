import os
import json
import time
import re
import argparse
from datetime import datetime, timezone
import requests

# NOTE: For YouTube comments, we recommend using a specialized library 
# like 'youtube-comment-downloader' because YouTube's comment loading 
# logic is complex (token-based AJAX).
# 
# Install with: pip install youtube-comment-downloader

try:
    from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_RECENT
except ImportError:
    YoutubeCommentDownloader = None

# ─── Configuration ───────────────────────────────────────────────────────────

CHANNELS = [
    "@DrAnujPachhel",
    "@mitali.this.side",
    "Doctor Ani",
    "Poorvi Sachan",
    "Advika Singh",
    "DocRocks"
]

SEARCH_QUERIES = [
    "First 24-hour internship duty vlog",
    "NEET PG hell week",
    "MBBS Intern Vlog in COVID-19 Ward",
    "Indian medical resident toxic culture",
    "MBBS student burnout India"
]

PAIN_POINT_KEYWORDS = [
    "exhausted", "burnout", "toxic", "senior", "ragging", "stipend", "duty", 
    "hours", "shift", "crying", "mental health", "depression", "quit", 
    "scut", "iv", "foley", "paperwork", "thesis", "spss", "neet pg", 
    "ini cet", "residency", "internship", "suicide", "hell", "unbearable",
    "stipend delay", "no sleep", "48 hours", "36 hours", "continuous duty"
]

# ─── Helper Functions ────────────────────────────────────────────────────────

def get_video_ids_from_search(query):
    """Search YouTube and return a list of video IDs."""
    print(f"  🔍 Searching YouTube for: '{query}'...")
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    try:
        response = requests.get(search_url, headers=headers, timeout=15)
        video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", response.text)
        return list(set(video_ids)) # Unique IDs
    except Exception as e:
        print(f"    ❌ Error searching: {e}")
        return []

def is_pain_point(text):
    """Check if the text contains medical community pain points."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in PAIN_POINT_KEYWORDS)

def format_lead(comment, video_id):
    """Format a YouTube comment into the Supabase 'leads' schema."""
    # created_at handling
    # The downloader might return relative time (e.g. '2 hours ago'). 
    # We'll use current time if we can't parse it easily.
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    return {
        "user_id": comment.get("author"),
        "pain_point": comment.get("text"),
        "email": None,
        "phone": None,
        "source": "youtube_comment",
        "created_at": now_str, # Default to now for simplicity
        "processed": False,
        "_meta": {
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "likes": comment.get("votes"),
            "time_text": comment.get("time")
        }
    }

# ─── Main Logic ──────────────────────────────────────────────────────────────

def scrape_youtube():
    if YoutubeCommentDownloader is None:
        print("\n❌ Error: 'youtube-comment-downloader' library not found.")
        print("Please install it using: pip install youtube-comment-downloader")
        return []

    downloader = YoutubeCommentDownloader()
    all_leads = []
    video_pool = set()

    # Phase 1: Collect Video IDs from Queries
    print(f"\n{'='*60}")
    print(f"📺 PHASE 1: Discovering Videos via Search")
    print(f"{'='*60}")
    for query in SEARCH_QUERIES:
        video_pool.update(get_video_ids_from_search(query))
        time.sleep(2) # Respectful delay

    # Phase 2: Collect Video IDs from Channels
    print(f"\n{'='*60}")
    print(f"📺 PHASE 2: Discovering Videos from Target Channels")
    print(f"{'='*60}")
    for channel in CHANNELS:
        video_pool.update(get_video_ids_from_search(channel + " vlogs"))
        time.sleep(2)

    print(f"\n✅ Total unique videos found: {len(video_pool)}")
    
    # Phase 3: Extract Comments
    print(f"\n{'='*60}")
    print(f"💬 PHASE 3: Extracting & Filtering Comments")
    print(f"{'='*60}")
    
    # Limit to top N videos to avoid getting blocked or taking too long
    # In a real run, you might want to process more.
    videos_to_process = list(video_pool)[:20] 
    
    for video_id in videos_to_process:
        print(f"  📥 Processing video: {video_id}...")
        count = 0
        try:
            comments = downloader.get_comments(video_id, sort_by=SORT_BY_RECENT)
            for comment in comments:
                text = comment.get("text", "")
                if is_pain_point(text):
                    lead = format_lead(comment, video_id)
                    all_leads.append(lead)
                    count += 1
                
                # Safety stop per video
                if count >= 50: break 
            
            print(f"    ✨ Found {count} pain points.")
            time.sleep(3) # Delay between videos
        except Exception as e:
            print(f"    ❌ Error getting comments for {video_id}: {e}")

    return all_leads

def save_results(leads):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "scraped_youtube_leads.json")
    supabase_file = os.path.join(script_dir, "scraped_youtube_leads_supabase_ready.json")

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
    print(f"📊 YOUTUBE SCRAPING SUMMARY")
    print(f"{'='*60}")
    print(f"  Total leads:           {len(leads)}")
    print(f"  💾 Full output:        {output_file}")
    print(f"  💾 Supabase-ready:     {supabase_file}")

if __name__ == "__main__":
    leads = scrape_youtube()
    if leads:
        save_results(leads)
    else:
        print("\nNo leads found or script failed. Ensure 'youtube-comment-downloader' is installed.")
