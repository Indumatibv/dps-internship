# Facebook Medical Pain Point Scraper

This script scrapes public Facebook pages and groups related to the Indian medical community and extracts posts containing clinical pain points, formatted for the Supabase `leads` table.

## Approach

Facebook does **not** have a public JSON API like Reddit. This script uses **mbasic.facebook.com** (Facebook's lightweight mobile site) and parses the HTML with BeautifulSoup to extract post content.

> ⚠️ **Important**: Facebook aggressively blocks unauthenticated scraping. If you get 0 leads, see the "Troubleshooting" section below.

## Features

- **Targeted Pages & Groups**: Focuses on Indian medical communities like `MedicalDialogues`, `IndianMedicalAssociation`, `ResidentDoctorsAssociation`, etc.
- **Same Pain Point Keywords**: Uses the exact same keyword list and 8-category classification as the Reddit scraper (bureaucratic, workload, toxic culture, clinical scut, research, exam stress, financial, emotional).
- **Pagination**: Follows "See More Posts" links (up to 5 pages per target).
- **Supabase Ready**: Outputs JSON data ready for the `leads` table with `source='facebook'`.

## Files

| File | Description |
|------|-------------|
| `scrape_facebook_med.py` | Main scraping script |
| `push_to_supabase.py` | Pushes scraped leads to Supabase |
| `Facebook_Flow_Explained.md` | Detailed explanation of how the scraper works |
| `requirements.txt` | Python dependencies |

## Setup

1. Install dependencies:
   ```bash
   pip install -r Facebook/requirements.txt
   ```

2. Run the scraper:
   ```bash
   python Facebook/scrape_facebook_med.py
   ```

3. Push results to Supabase:
   ```bash
   python Facebook/push_to_supabase.py
   ```

## Output Files

- `scraped_facebook_leads.json` — Full data with metadata (categories, timestamps)
- `scraped_facebook_leads_supabase_ready.json` — Clean format ready for Supabase upload

## Troubleshooting

If you consistently get **0 leads**, Facebook's login wall is blocking access. Two options:

1. **Add session cookies**: Log into Facebook in your browser, copy your session cookies, and paste them into the `COOKIES` dict in `scrape_facebook_med.py`.
2. **Use Selenium**: Switch to a browser automation approach that handles login and JS rendering.
