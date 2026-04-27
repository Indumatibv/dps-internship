# How the LinkedIn Scraper Works (In Easy Terms)

This document explains how our `LinkedIn/scrape_linkedin_med.py` script attempts to gather professional insights.

---

### Step 1: Targeting Specific Professional Profiles
Unlike Reddit (which is anonymous) or YouTube (which is video-focused), LinkedIn is professional. We target specific Company Pages (like *Medical Dialogues*) and Influential Doctors (like *Dr. Shrey Bhatia*) who discuss the **systemic** issues in medicine.

### Step 2: "Reading" the Page
The script acts like a browser without a screen. It goes to those specific URLs and downloads the underlying HTML code of the page. It then uses a tool called `BeautifulSoup` to sift through the code and extract all the visible text paragraphs.

### Step 3: Filtering for "Formal" Pain Points
While Reddit has rants about "toxic seniors", LinkedIn posts are usually more formal. The script looks for keywords tailored to this environment:
- *"clerical work"*
- *"burden"*
- *"burnout survey"*
- *"admin work"*

If a paragraph mentions these, it's saved as a lead.

### Step 4: Formatting for Supabase
Just like the other scrapers, it extracts the `user_id` from the URL, saves the text as the `pain_point`, and labels the `source` as `linkedin`. It saves this cleanly into `scraped_linkedin_leads_supabase_ready.json`.

---

### ⚠️ The "Auth Wall" Problem
LinkedIn is **very** protective of its data. If you browse LinkedIn in an incognito window, you'll quickly notice it forces you to log in to read posts. 

Because our simple script doesn't log in, LinkedIn will often block it and return a "Login Page" instead of the actual posts. When this happens, the script will find 0 leads. If this occurs consistently, the scraping strategy must be upgraded to use **Browser Automation** (where a real browser logs in with an account before scraping).
