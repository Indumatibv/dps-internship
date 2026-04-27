# How the Reddit Scraper Works (In Easy Terms)

This document explains exactly how our `scrape_indian_med.py` script gathers data from Reddit, broken down into 5 simple steps.

---

### Step 1: Choosing Where to Look (The Subreddits)
We don't search the whole internet. We gave the script a specific list of "neighborhoods" (subreddits) where Indian medical students and doctors hang out. 
- Example: `r/IndianMedSchool`, `r/Residency`, `r/MBBSindia`.

### Step 2: Gathering Posts (Two Different Ways)
Once the script enters a subreddit, it uses two different methods to find posts:
1. **Browsing the Front Page:** It looks at the "Hot", "New", and "Top" posts, just like a normal user scrolling through their feed.
2. **Using the Search Bar:** It actively searches for specific phrases like *"toxic seniors"*, *"LAMA DAMA"*, or *"duty hours"* to dig up older or hidden posts that match our exact needs.

### Step 3: Filtering for "Pain Points"
The script downloads a lot of posts, but we only want the ones where people are complaining or struggling. 
To do this, it reads the title and the body of the post and looks for **Keywords**. 
- If a post mentions words like *"exhausting"*, *"scut work"*, *"ragging"*, or *"thesis"*, the script flags it as a "Pain Point". 
- If it doesn't contain our keywords, the script ignores it and moves on.

### Step 4: Categorizing the Complaints
When the script finds a "Pain Point", it tries to understand *what kind* of problem it is based on the words used. 
- Mentioned "paperwork" or "logbook"? -> Tags it as **Bureaucratic**.
- Mentioned "sleep deprivation"? -> Tags it as **Workload**.
- Mentioned "NEET PG"? -> Tags it as **Exam Stress**.

### Step 5: Saving the Data for Supabase
Finally, the script takes all the good posts it found and cleans them up. It saves them into two files:
1. `scraped_leads.json`: The raw data with extra details (like how many upvotes it had).
2. `scraped_leads_supabase_ready.json`: A stripped-down, perfectly formatted list. It makes sure every post has a `user_id`, the text of the `pain_point`, and a `source` tag saying "reddit". This file is ready to be uploaded directly into our Supabase database.

---

### A Note on "Rate Limiting" (Why it sometimes pauses)
Reddit has a security guard that stops people from downloading too much, too fast. To avoid getting banned, our script takes deliberate pauses (like waiting 2 to 5 seconds between clicks). If Reddit says "Slow down!", the script is smart enough to wait 15 seconds before trying again.
