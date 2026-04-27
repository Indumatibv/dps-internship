"""
Reddit Pain Point Scraper — Indian Medical Community
=====================================================
Targets specific Indian medical subreddits and scrapes posts/comments
related to clinical pain points, formatted for the Supabase `leads` table.

Usage:
    python3 Reddit/scrape_indian_med.py [--search-only] [--browse-only]

Output:
    scraped_leads.json  — ready for Supabase ingestion
"""

import requests
import json
import time
import argparse
import math
from datetime import datetime, timezone

# ─── Configuration ───────────────────────────────────────────────────────────

HEADERS = {"User-Agent": "IndianMedPainPointScraper/2.0 (research project)"}

# Primary target subreddits
SUBREDDITS = {
    # Tier 1 — India-specific medical
    "IndianMedSchool":    {"tier": 1, "desc": "Central node: interns, PG residents, attendings"},
    "MBBSindia":          {"tier": 1, "desc": "MBBS students, state hospital issues"},
    "doctorsindia":       {"tier": 1, "desc": "Indian doctors community"},
    "medicosindia":       {"tier": 1, "desc": "Indian medicos community"},
    "MedSchoolAnkiIndia": {"tier": 1, "desc": "Anki/spaced repetition for Indian curriculum"},
    # Tier 2 — Global with Indian presence
    "Residency":          {"tier": 2, "desc": "Global residency, significant Indian presence"},
    "AskAcademia":        {"tier": 2, "desc": "Global academia, SPSS/thesis pain points"},
}

# Search queries tailored to Indian medical pain points
SEARCH_QUERIES = [
    # Bureaucratic / paperwork pain
    "LAMA DAMA discharge summary",
    "paperwork burden intern",
    "case summary documentation",
    "logbook signatures internship",
    # Workload / toxic culture
    "residency toxic seniors ragging",
    "overworked duty hours resident",
    "scut work IVs Foley tubes",
    "sleep deprivation residency",
    "workload burnout PG",
    # Thesis / research struggles
    "SPSS thesis reproducibility",
    "thesis submission deadline",
    "research methodology frustration",
    # Exam prep exhaustion
    "NEET PG preparation stress",
    "INI CET exam anxiety",
    "Marrow PrepLadder exhaustion",
    # Stipend / financial
    "stipend delay resident",
    "non academic junior resident",
    # General pain points
    "frustrating internship experience India",
    "broken healthcare system India",
    "hospital bureaucracy India",
]

# Pain point keyword matching — broad enough to catch relevant content
PAIN_POINT_KEYWORDS = [
    # Bureaucratic
    "paperwork", "paper work", "lama", "dama", "discharge summary",
    "case summary", "bureaucratic", "documentation", "logbook", "signatures",
    # Workload
    "workload", "overworked", "duty hours", "sleep depriv", "burnout",
    "exhausting", "exhausted", "overwhelm", "hectic",
    # Toxic culture
    "ragging", "toxic", "senior", "bully", "humiliat",
    # Clinical scut
    "scut work", "ivs", "foley", "dressing",
    # Research / thesis
    "spss", "thesis", "reproducibility", "menu clicks", "research methodology",
    # Exam stress
    "neet pg", "ini cet", "preparation stress", "exam anxiety",
    "marrow", "prepladder",
    # Financial
    "stipend", "non-academic jr", "non academic jr", "salary delay",
    # Emotional / systemic
    "frustrat", "vent", "struggle", "broken system", "helpless",
    "dead inside", "mental health", "panic attack", "anxiety",
    "residency heavy", "residency hard", "internship hard",
]

# Rate limiting config
DELAY_BETWEEN_REQUESTS = 2.0   # seconds between Reddit API calls
DELAY_BETWEEN_SUBREDDITS = 3.0 # seconds between subreddits
MAX_RETRIES = 3


# ─── Reddit API Helpers ─────────────────────────────────────────────────────

def reddit_get(url, params=None, retries=MAX_RETRIES):
    """Make a GET request to Reddit with retry + backoff."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                wait = (attempt + 1) * 5
                print(f"    ⏳ Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            elif resp.status_code == 403:
                print(f"    🔒 Forbidden (subreddit may be private/non-existent): {url}")
                return None
            elif resp.status_code == 404:
                print(f"    ❌ Not found: {url}")
                return None
            else:
                print(f"    ⚠️  HTTP {resp.status_code} for {url}")
                time.sleep(2)
        except requests.exceptions.Timeout:
            print(f"    ⏱  Timeout (attempt {attempt + 1}/{retries})")
            time.sleep(3)
        except Exception as e:
            print(f"    ❗ Error: {e}")
            time.sleep(2)
    return None


# ─── Scraping Functions ─────────────────────────────────────────────────────

def browse_subreddit(subreddit, limit=50):
    """Browse hot + new feeds of a subreddit and return post metadata."""
    posts = []
    for category in ["hot", "new", "top"]:
        params = {"limit": limit}
        if category == "top":
            params["t"] = "month"  # top posts from last month

        url = f"https://www.reddit.com/r/{subreddit}/{category}.json"
        data = reddit_get(url, params)
        if data and "data" in data:
            for child in data["data"]["children"]:
                posts.append(child["data"])
        time.sleep(DELAY_BETWEEN_REQUESTS)
    return posts


def search_subreddit(subreddit, query, limit=10):
    """Search within a subreddit for a specific query."""
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": query,
        "sort": "relevance",
        "limit": limit,
        "type": "link",
        "t": "all",
        "restrict_sr": 1,
    }
    data = reddit_get(url, params)
    if data and "data" in data:
        return [child["data"] for child in data["data"]["children"]]
    return []


def fetch_post_comments(subreddit, post_id, limit=25):
    """Fetch top-level comments for a post."""
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
    params = {"limit": limit}
    data = reddit_get(url, params)
    if not data or len(data) < 2:
        return []
    
    comments = []
    for child in data[1]["data"]["children"]:
        if child.get("kind") == "t1":
            cdata = child["data"]
            body = cdata.get("body", "")
            if body not in ("[deleted]", "[removed]", ""):
                comments.append(cdata)
    return comments


# ─── Pain Point Detection ───────────────────────────────────────────────────

def is_pain_point(text):
    """Check if text contains pain point keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in PAIN_POINT_KEYWORDS)


def classify_pain_point(text):
    """Return a list of matched pain point categories."""
    if not text:
        return []
    text_lower = text.lower()
    categories = {
        "bureaucratic":  ["paperwork", "paper work", "lama", "dama", "discharge summary",
                          "case summary", "bureaucratic", "documentation", "logbook"],
        "workload":      ["workload", "overworked", "duty hours", "sleep depriv", 
                          "burnout", "exhausting", "overwhelm", "hectic"],
        "toxic_culture": ["ragging", "toxic", "bully", "humiliat"],
        "clinical_scut": ["scut work", "ivs", "foley", "dressing"],
        "research":      ["spss", "thesis", "reproducibility", "menu clicks"],
        "exam_stress":   ["neet pg", "ini cet", "preparation stress", "marrow", "prepladder"],
        "financial":     ["stipend", "non-academic jr", "salary delay"],
        "emotional":     ["frustrat", "struggle", "helpless", "dead inside", 
                          "mental health", "panic attack", "anxiety"],
    }
    matched = []
    for cat, keywords in categories.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(cat)
    return matched


# ─── Lead Formatting ────────────────────────────────────────────────────────

def format_lead(item, subreddit, source_type="post"):
    """Format a Reddit post/comment as a lead matching the Supabase schema."""
    created_utc = item.get("created_utc")
    created_at = (datetime.fromtimestamp(created_utc, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                  if created_utc else datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))

    if source_type == "post":
        title = item.get("title", "")
        body = item.get("selftext", "")
        pain_text = f"{title}\n\n{body}".strip()
        permalink = item.get("permalink", "")
    else:
        pain_text = item.get("body", "").strip()
        permalink = item.get("permalink", "")

    categories = classify_pain_point(pain_text)

    return {
        "user_id":      item.get("author", "[deleted]"),
        "pain_point":   pain_text,
        "email":        None,
        "phone":        None,
        "source":       f"https://www.reddit.com{permalink}",
        "created_at":   created_at,
        "processed":    False,
        # Extra metadata (not in Supabase schema, but useful for analysis)
        "_meta": {
            "subreddit":   subreddit,
            "source_type": source_type,
            "score":       item.get("score", 0),
            "categories":  categories,
        }
    }


# ─── Main Pipeline ──────────────────────────────────────────────────────────

def scrape_all(do_browse=True, do_search=True):
    """Run the full scraping pipeline."""
    all_leads = []
    seen_ids = set()  # track by permalink to deduplicate

    def add_lead(lead):
        key = lead["source"]
        if key not in seen_ids:
            seen_ids.add(key)
            all_leads.append(lead)

    for subreddit, info in SUBREDDITS.items():
        tier = info["tier"]
        print(f"\n{'='*60}")
        print(f"📡 r/{subreddit} (Tier {tier}) — {info['desc']}")
        print(f"{'='*60}")

        # ── Phase 1: Browse hot/new/top ──────────────────────────────
        if do_browse:
            print(f"  📰 Browsing feeds...")
            posts = browse_subreddit(subreddit, limit=25 if tier == 1 else 15)
            print(f"     Found {len(posts)} posts from feeds")

            pain_posts = []
            for post in posts:
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                combined = f"{title} {selftext}"
                if is_pain_point(combined):
                    pain_posts.append(post)
                    add_lead(format_lead(post, subreddit, "post"))

            print(f"     🎯 {len(pain_posts)} pain-point posts matched")

            # Fetch comments for top pain-point posts (limit to avoid rate limits)
            comment_posts = sorted(pain_posts, 
                                   key=lambda p: p.get("num_comments", 0), 
                                   reverse=True)[:5]
            for post in comment_posts:
                comments = fetch_post_comments(subreddit, post["id"], limit=15)
                for comment in comments:
                    if is_pain_point(comment.get("body", "")):
                        add_lead(format_lead(comment, subreddit, "comment"))
                time.sleep(DELAY_BETWEEN_REQUESTS)

        # ── Phase 2: Search queries ──────────────────────────────────
        if do_search:
            print(f"  🔍 Running search queries...")
            for query in SEARCH_QUERIES:
                results = search_subreddit(subreddit, query, limit=5)
                for post in results:
                    title = post.get("title", "")
                    selftext = post.get("selftext", "")
                    combined = f"{title} {selftext}"
                    if is_pain_point(combined):
                        add_lead(format_lead(post, subreddit, "post"))
                time.sleep(DELAY_BETWEEN_REQUESTS)
            print(f"     Search complete.")

        print(f"  📊 Running total: {len(all_leads)} leads")
        time.sleep(DELAY_BETWEEN_SUBREDDITS)

    return all_leads


def save_results(leads, output_file="scraped_leads.json"):
    """Save leads to JSON, separating Supabase-ready data from metadata."""
    # Full output with metadata
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    # Supabase-ready output (strip _meta)
    supabase_leads = []
    for lead in leads:
        clean = {k: v for k, v in lead.items() if k != "_meta"}
        supabase_leads.append(clean)

    supabase_file = output_file.replace(".json", "_supabase_ready.json")
    with open(supabase_file, "w", encoding="utf-8") as f:
        json.dump(supabase_leads, f, indent=2, ensure_ascii=False)

    # Summary stats
    categories_count = {}
    for lead in leads:
        for cat in lead.get("_meta", {}).get("categories", []):
            categories_count[cat] = categories_count.get(cat, 0) + 1

    print(f"\n{'='*60}")
    print(f"📊 SCRAPING SUMMARY")
    print(f"{'='*60}")
    print(f"  Total leads:           {len(leads)}")
    print(f"  Unique subreddits:     {len(set(l['_meta']['subreddit'] for l in leads if '_meta' in l))}")
    print(f"  Posts vs Comments:     "
          f"{sum(1 for l in leads if l.get('_meta', {}).get('source_type') == 'post')} / "
          f"{sum(1 for l in leads if l.get('_meta', {}).get('source_type') == 'comment')}")
    print(f"\n  Pain point categories:")
    for cat, count in sorted(categories_count.items(), key=lambda x: -x[1]):
        print(f"    {cat:20s} → {count}")
    print(f"\n  💾 Full output:        {output_file}")
    print(f"  💾 Supabase-ready:     {supabase_file}")


if __name__ == "__main__":
    # Resolve paths relative to this script's directory
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "scraped_leads.json")

    parser = argparse.ArgumentParser(description="Scrape Indian medical subreddits for pain points")
    parser.add_argument("--search-only", action="store_true", help="Only run search queries, skip browsing")
    parser.add_argument("--browse-only", action="store_true", help="Only browse feeds, skip search")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output file path")
    args = parser.parse_args()

    do_browse = not args.search_only
    do_search = not args.browse_only

    leads = scrape_all(do_browse=do_browse, do_search=do_search)
    save_results(leads, args.output)
