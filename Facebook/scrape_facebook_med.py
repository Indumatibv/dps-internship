"""
Facebook Pain Point Scraper — Indian Medical Community
=======================================================
Scrapes public Facebook pages and groups related to Indian medical
professionals and extracts posts containing clinical pain points,
formatted for the Supabase `leads` table.

Approach:
    Facebook does not have a simple .json endpoint like Reddit.
    This script uses mobile.facebook.com (mbasic) HTML scraping with
    BeautifulSoup, which provides a lightweight, JS-free HTML page
    that is easier to parse than the full desktop site.

    ⚠️ NOTE: Facebook aggressively blocks unauthenticated scraping.
    If you get 0 leads, consider adding cookies from a logged-in
    session (see COOKIES dict below) or switching to a Selenium-based
    approach.

Usage:
    python3 Facebook/scrape_facebook_med.py [--output FILE]

Output:
    scraped_facebook_leads.json              — full data with metadata
    scraped_facebook_leads_supabase_ready.json — ready for Supabase
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import argparse
import os
import re
from datetime import datetime, timezone

# ─── Configuration ───────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# If you have a logged-in session, paste your cookie string here.
# e.g. COOKIES = {"cookie": "c_user=...; xs=...; ..."}
# Leave empty for unauthenticated scraping (limited results).
COOKIES = {}

BASE_URL = "https://mbasic.facebook.com"

# ─── Target Pages & Groups ──────────────────────────────────────────────────
# These are public Facebook pages/groups related to Indian medical community.
# Format: {"slug": {"type": "page"|"group", "desc": "..."}}

TARGETS = {
    # ── Pages ──
    "MedicalDialogues": {
        "type": "page",
        "desc": "Medical news and discussions for Indian doctors",
    },
    "DoctorsForDoctors": {
        "type": "page",
        "desc": "Peer support community for Indian doctors",
    },
    "IndianMedicalAssociation": {
        "type": "page",
        "desc": "IMA official page — policy, workload, and systemic issues",
    },
    "ResidentDoctorsAssociation": {
        "type": "page",
        "desc": "Resident doctors advocacy — duty hours, stipends, conditions",
    },
    "MBBSStudentsIndia": {
        "type": "page",
        "desc": "MBBS students community — exam stress, internship issues",
    },
    "NEETPGAspirants": {
        "type": "page",
        "desc": "NEET PG preparation community",
    },
    # ── Groups (public) ──
    "groups/IndianDoctorsForum": {
        "type": "group",
        "desc": "Open forum for Indian doctors to discuss challenges",
    },
    "groups/MBBSHelpline": {
        "type": "group",
        "desc": "MBBS students helpline — academic and emotional support",
    },
}

# ─── Pain Point Keywords (same as Reddit scraper) ───────────────────────────

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
DELAY_BETWEEN_REQUESTS = 3.0   # seconds between page fetches
DELAY_BETWEEN_TARGETS = 5.0    # seconds between different pages/groups
MAX_PAGES_PER_TARGET = 5       # how many "See More" pages to follow
MAX_RETRIES = 3


# ─── HTTP Helpers ────────────────────────────────────────────────────────────

def fb_get(url, retries=MAX_RETRIES):
    """Make a GET request to Facebook mbasic with retry + backoff."""
    for attempt in range(retries):
        try:
            resp = requests.get(
                url,
                headers=HEADERS,
                cookies=COOKIES,
                timeout=20,
                allow_redirects=True,
            )
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 429:
                wait = (attempt + 1) * 10
                print(f"    ⏳ Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            elif resp.status_code in (302, 303):
                print(f"    🔒 Redirected (login wall likely): {url}")
                return None
            elif resp.status_code == 404:
                print(f"    ❌ Not found: {url}")
                return None
            else:
                print(f"    ⚠️  HTTP {resp.status_code} for {url}")
                time.sleep(3)
        except requests.exceptions.Timeout:
            print(f"    ⏱  Timeout (attempt {attempt + 1}/{retries})")
            time.sleep(5)
        except Exception as e:
            print(f"    ❗ Error: {e}")
            time.sleep(3)
    return None


# ─── Parsing Functions ──────────────────────────────────────────────────────

def parse_posts_from_html(html):
    """
    Parse mbasic.facebook.com HTML and extract post texts + metadata.
    Returns a list of dicts with keys: text, author, link, timestamp_raw.
    """
    soup = BeautifulSoup(html, "html.parser")
    posts = []

    # mbasic uses <div> with specific data attributes or class patterns for posts
    # The structure varies, so we try multiple selectors.

    # Strategy 1: Look for article-like containers
    post_containers = soup.find_all("article")

    # Strategy 2: If no <article> tags, look for story divs
    if not post_containers:
        post_containers = soup.find_all("div", {"data-ft": True})

    # Strategy 3: Fallback — look for divs with post-like structure
    if not post_containers:
        # mbasic often wraps posts in divs with id starting with "u_"
        post_containers = soup.find_all("div", id=re.compile(r"^u_"))

    for container in post_containers:
        # Extract post text
        # mbasic puts the actual post text in <p> or <span> tags within the container
        text_parts = []
        for p in container.find_all(["p", "span"]):
            text = p.get_text(strip=True)
            if text and len(text) > 10:  # skip tiny fragments
                text_parts.append(text)

        post_text = " ".join(text_parts).strip()
        if not post_text or len(post_text) < 20:
            continue

        # Extract author (usually the first <strong> or <h3> link)
        author = "[unknown]"
        author_tag = container.find("strong")
        if author_tag:
            author = author_tag.get_text(strip=True)
        else:
            h3 = container.find("h3")
            if h3:
                author = h3.get_text(strip=True)

        # Extract post link
        link = ""
        permalink_tag = container.find("a", href=re.compile(r"/story\.php|/permalink"))
        if permalink_tag:
            link = permalink_tag.get("href", "")
            if link.startswith("/"):
                link = f"https://www.facebook.com{link}"

        # Extract timestamp (mbasic uses <abbr> for timestamps)
        timestamp_raw = ""
        abbr = container.find("abbr")
        if abbr:
            timestamp_raw = abbr.get_text(strip=True)

        posts.append({
            "text": post_text,
            "author": author,
            "link": link,
            "timestamp_raw": timestamp_raw,
        })

    return posts


def find_next_page_url(html):
    """Find the 'See More Posts' / 'Show more' link for pagination."""
    soup = BeautifulSoup(html, "html.parser")

    # mbasic pagination links
    for a in soup.find_all("a", href=True):
        link_text = a.get_text(strip=True).lower()
        if any(phrase in link_text for phrase in [
            "see more", "show more", "more stories",
            "older posts", "next", "more posts"
        ]):
            href = a["href"]
            if href.startswith("/"):
                return f"{BASE_URL}{href}"
            elif href.startswith("http"):
                return href
    return None


# ─── Pain Point Detection (same logic as Reddit) ────────────────────────────

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

def format_lead(post, target_slug):
    """Format a Facebook post as a lead matching the Supabase schema."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    pain_text = post["text"]
    categories = classify_pain_point(pain_text)

    source_url = post.get("link", "")
    if not source_url:
        source_url = f"https://www.facebook.com/{target_slug}"

    return {
        "user_id":    post.get("author", "[unknown]"),
        "pain_point": pain_text,
        "email":      None,
        "phone":      None,
        "source":     source_url,
        "created_at": now,
        "processed":  False,
        # Extra metadata
        "_meta": {
            "target":        target_slug,
            "source_type":   "facebook_post",
            "timestamp_raw": post.get("timestamp_raw", ""),
            "categories":    categories,
        }
    }


# ─── Scraping Pipeline ──────────────────────────────────────────────────────

def scrape_target(slug, info):
    """Scrape a single Facebook page/group for pain point posts."""
    target_type = info["type"]
    all_posts = []

    # Build the initial URL
    url = f"{BASE_URL}/{slug}"
    print(f"  🌐 Fetching: {url}")

    page_count = 0
    while url and page_count < MAX_PAGES_PER_TARGET:
        html = fb_get(url)
        if not html:
            print(f"    ❌ Failed to fetch page {page_count + 1}")
            break

        # Check for login wall
        if "login" in html.lower()[:500] and "password" in html.lower()[:1000]:
            print(f"    🔒 Login wall detected. Unauthenticated scraping may not work.")
            print(f"       Consider adding session cookies to COOKIES dict.")
            break

        posts = parse_posts_from_html(html)
        all_posts.extend(posts)
        print(f"    📄 Page {page_count + 1}: found {len(posts)} posts")

        # Find next page
        url = find_next_page_url(html)
        page_count += 1

        if url:
            time.sleep(DELAY_BETWEEN_REQUESTS)

    return all_posts


def scrape_all():
    """Run the full scraping pipeline across all targets."""
    all_leads = []
    seen_texts = set()  # deduplicate by text hash

    def add_lead(lead):
        # Use first 200 chars of pain_point text as dedup key
        key = lead["pain_point"][:200]
        if key not in seen_texts:
            seen_texts.add(key)
            all_leads.append(lead)

    for slug, info in TARGETS.items():
        print(f"\n{'='*60}")
        print(f"📡 {slug} ({info['type']}) — {info['desc']}")
        print(f"{'='*60}")

        posts = scrape_target(slug, info)
        print(f"  📰 Total posts scraped: {len(posts)}")

        # Filter for pain points
        pain_count = 0
        for post in posts:
            if is_pain_point(post["text"]):
                add_lead(format_lead(post, slug))
                pain_count += 1

        print(f"  🎯 Pain-point posts matched: {pain_count}")
        print(f"  📊 Running total: {len(all_leads)} leads")

        time.sleep(DELAY_BETWEEN_TARGETS)

    return all_leads


# ─── Save Results ────────────────────────────────────────────────────────────

def save_results(leads, output_file):
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
    print(f"  Unique targets:        {len(set(l['_meta']['target'] for l in leads if '_meta' in l))}")
    print(f"\n  Pain point categories:")
    for cat, count in sorted(categories_count.items(), key=lambda x: -x[1]):
        print(f"    {cat:20s} → {count}")
    print(f"\n  💾 Full output:        {output_file}")
    print(f"  💾 Supabase-ready:     {supabase_file}")


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Resolve paths relative to this script's directory
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "scraped_facebook_leads.json")

    parser = argparse.ArgumentParser(
        description="Scrape Facebook pages/groups for Indian medical pain points"
    )
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT,
        help="Output file path (default: Facebook/scraped_facebook_leads.json)"
    )
    args = parser.parse_args()

    print("🚀 Facebook Medical Pain Point Scraper")
    print("=" * 60)
    print("⚠️  NOTE: Facebook heavily restricts unauthenticated scraping.")
    print("   If you get 0 leads, add session cookies to the COOKIES dict")
    print("   in the script, or switch to a Selenium-based approach.")
    print("=" * 60)

    leads = scrape_all()
    save_results(leads, args.output)
