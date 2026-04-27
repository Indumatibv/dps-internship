# LinkedIn Medical Pain Point Scraper

This script attempts to extract formal discussions of pain points (such as clerical work burden, burnout statistics) from targeted LinkedIn profiles and company pages.

## Features

- **Targeted Profiles**: Focuses on specific URLs like `medical-dialogues` and `dr-shrey-bhatia-md`.
- **Formal Pain Points**: Uses keywords tailored for professional networks (e.g., "clerical burden", "survey", "overworked").
- **Supabase Ready**: Outputs JSON data ready for the `leads` table with `source='linkedin'`.

## Setup

1. Install dependencies:
   ```bash
   pip install -r LinkedIn/requirements.txt
   ```

2. Run the scraper:
   ```bash
   python LinkedIn/scrape_linkedin_med.py
   ```

## Important Note on LinkedIn Scraping
LinkedIn has extremely aggressive anti-scraping measures. Unauthenticated requests (like those made by this script) are frequently redirected to an "Auth Wall" (Login page) or blocked entirely (HTTP 999 or 429). 
If you consistently get 0 leads or 999 errors, you will need to implement a more advanced browser automation tool (like Selenium) to log in and scrape.
