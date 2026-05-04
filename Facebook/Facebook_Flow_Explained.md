
# How the Facebook Scraper Works (In Easy Terms)

This document explains how our `scrape_facebook_med.py` script gathers medical pain point data from Facebook.

---

## Method: mbasic HTML Scraping

Unlike Reddit (which has a simple `.json` endpoint), Facebook does **not** offer a public JSON API for pages/groups.

We use **mbasic.facebook.com** — Facebook's lightweight mobile site — because:
- It serves simple HTML with no JavaScript required
- It's much easier to parse than the full desktop site
- It has a cleaner DOM structure for extracting post text

**Comparison with other methods:**

| Method | Pros | Cons |
|--------|------|------|
| **mbasic HTML (our method)** | No JS needed, lightweight | Blocked by login wall for most content |
| **Graph API** | Official, reliable | Requires app review + access tokens; most page/group data is now restricted |
| **Selenium/Playwright** | Can handle login, JS rendering | Heavy, slow, needs browser; risk of account ban |
| **CrowdTangle** | Academic/research access to public posts | Shutting down; limited availability |

---

## Step-by-Step Flow

### Step 1: Choosing Where to Look (Target Pages & Groups)
We have a curated list of **public** Facebook pages and groups where Indian medical professionals discuss challenges:
- `MedicalDialogues`, `DoctorsForDoctors`, `IndianMedicalAssociation`
- `ResidentDoctorsAssociation`, `MBBSStudentsIndia`, `NEETPGAspirants`
- Public groups like `IndianDoctorsForum`, `MBBSHelpline`

### Step 2: Fetching Posts
For each target, the script:
1. Loads the mbasic page/group URL
2. Parses the HTML with BeautifulSoup to extract post text, author, and links
3. Follows "See More Posts" pagination links (up to 5 pages per target)

### Step 3: Filtering for Pain Points
Exactly the same keyword matching as the Reddit scraper. The script checks each post for keywords like:
- *"paperwork"*, *"burnout"*, *"duty hours"*, *"ragging"*, *"thesis"*, etc.
- If a post matches, it's kept. Otherwise it's skipped.

### Step 4: Categorizing the Complaints
Same 8-category classification as Reddit:
- **Bureaucratic** → paperwork, logbook, discharge summary
- **Workload** → duty hours, burnout, sleep deprivation
- **Toxic Culture** → ragging, bullying, humiliation
- **Clinical Scut** → scut work, IVs, dressings
- **Research** → thesis, SPSS, reproducibility
- **Exam Stress** → NEET PG, INI CET, Marrow, PrepLadder
- **Financial** → stipend delay, salary issues
- **Emotional** → mental health, anxiety, frustration

### Step 5: Saving the Data
Two JSON files are generated:
1. `scraped_facebook_leads.json` — full data with metadata (categories, timestamps)
2. `scraped_facebook_leads_supabase_ready.json` — clean format ready for Supabase upload

---

## Important: Facebook's Anti-Scraping Measures

Facebook is **much more aggressive** than Reddit at blocking scrapers:
- Most page/group content requires a logged-in session
- Unauthenticated requests often hit a login wall immediately
- IP-based rate limiting is strict

**If you get 0 leads**, you have two options:
1. **Add cookies**: Log into Facebook in your browser, copy your session cookies, and paste them into the `COOKIES` dict in the script.
2. **Use Selenium**: Switch to a browser automation approach that can handle login and JS rendering.
