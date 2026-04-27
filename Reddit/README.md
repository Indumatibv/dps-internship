# Reddit Medical Pain Point Scraper

This module scrapes medical-related subreddits (specifically focused on the Indian medical community) to identify and extract "pain points" from posts and comments. The goal is to gather insights into the challenges faced by medical students, interns, and residents — and format them as leads for a Supabase database.

## Features

- **Targeted Scraping**: Focuses on subreddits like `r/IndianMedSchool`, `r/MBBSindia`, `r/Residency`, etc.
- **Pain Point Detection**: Uses a keyword-based approach to identify relevant frustrations, bureaucratic hurdles, and workload issues.
- **Lead Generation**: Formats the scraped data to match a Supabase `leads` table schema for future integration.
- **JSON Storage**: Saves results as `scraped_leads.json` and `scraped_leads_supabase_ready.json`.

## Setup

1. Install dependencies (from project root):
   ```bash
   pip install -r requirements.txt
   ```

2. Run the scraper:
   ```bash
   python Reddit/scrape_indian_med.py
   ```

3. Push to Supabase (when ready):
   ```bash
   export SUPABASE_KEY='your-anon-public-key'
   python Reddit/push_to_supabase.py
   ```

---

## Scraping Approach & Methodology

The scraping process is designed to be targeted, robust, and respectful of Reddit's API rate limits. It operates in several phases:

### 1. Targeted Subreddit Selection
The scraper focuses on curated subreddits categorized into tiers:
- **Tier 1 (India-Specific):** `r/IndianMedSchool`, `r/MBBSindia`, `r/doctorsindia`, `r/medicosindia`, `r/MedSchoolAnkiIndia`
- **Tier 2 (Global with Indian Presence):** `r/Residency`, `r/AskAcademia`

### 2. Dual Discovery Mechanism
To ensure a comprehensive dataset, the script uses two methods to find relevant content:
- **Feed Browsing:** Scrapes the `hot`, `new`, and `top` (past month) feeds to capture recent and highly engaging discussions.
- **Targeted Searching:** Executes specific query searches (e.g., "LAMA DAMA discharge summary", "residency toxic seniors ragging") to find historical or niche complaints that might not be on the front page.

### 3. Pain Point Detection & Categorization
Not every post is a complaint. The script analyzes the title and body text of posts and comments against a predefined list of keywords to identify true "pain points".
When a match is found, the content is categorized into one or more themes:
- `bureaucratic` (paperwork, logbooks)
- `workload` (sleep deprivation, duty hours)
- `toxic_culture` (ragging, humiliation)
- `clinical_scut` (IVs, Foley tubes)
- `research` (thesis issues, SPSS)
- `exam_stress` (NEET PG, INI CET)
- `financial` (stipend delays)
- `emotional` (burnout, mental health)

### 4. Robust Rate Limiting
Reddit's public `.json` endpoints have strict rate limits. The scraper implements:
- Delays between individual API requests.
- Longer delays between switching subreddits.
- **Exponential Backoff:** If Reddit returns a 429 (Too Many Requests) error, the script automatically pauses and waits progressively longer before retrying.

---

## Data Schema (Supabase `leads` table)

| Field | Description |
|-------|-------------|
| `user_id` | Reddit username |
| `pain_point` | The content of the post or comment |
| `email` | Null (placeholder for future use) |
| `phone` | Null (placeholder for future use) |
| `source` | Set to "reddit" for all entries |
| `created_at` | Timestamp of the original post |
| `processed` | Boolean flag (default: false) |

---

## File Structure

| File | Description |
|------|-------------|
| `scrape_indian_med.py` | The main scraping engine |
| `push_to_supabase.py` | Utility to upload cleaned data to Supabase |
| `scraped_leads.json` | Complete raw output with metadata, categories, and scores |
| `scraped_leads_supabase_ready.json` | Formatted output matching the Supabase `leads` table schema |
| `test.py` | Older scraping approach using local LLMs (Mistral/Ollama) for dynamic search queries |

---

## Usage Commands

**Run the full scraper (browse feeds + search queries):**
```bash
python scrape_indian_med.py
```

**Run search queries only (faster, less prone to rate limits):**
```bash
python scrape_indian_med.py --search-only
```

**Run feed browsing only (skip search):**
```bash
python scrape_indian_med.py --browse-only
```

**Push to Supabase:**
```bash
export SUPABASE_KEY='your-anon-public-key'
python push_to_supabase.py
```
