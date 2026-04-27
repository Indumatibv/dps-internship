# How the YouTube Scraper Works (In Easy Terms)

This document explains how our `YouTube/scrape_youtube_med.py` script turns YouTube comments into valuable leads for Supabase.

---

### Step 1: Targeting Influencers
We don't just search randomly. We targeted specific YouTube channels that we know are popular with Indian medical students (like Dr. Anuj Pachhel and Mitali). These channels are like "hubs" where students share their real feelings.

### Step 2: Finding the Right Videos
The script looks for two things:
1. **Channel Vlogs**: It scans the most recent videos from our target channels.
2. **Specific Pain Point Topics**: It searches YouTube for keywords like *"First 24-hour internship duty"* or *"NEET PG hell week"* to find smaller creators who are sharing raw, unfiltered hospital experiences.

### Step 3: Digging into the Comments
The video itself is just the starting point. The **real value** is in the comment section. 
The script acts as an automated reader that scrolls through hundreds of comments under these videos. It treats the comment section like a "digital focus group" where people share their own struggles in response to the video.

### Step 4: Filtering for "Emotional Gold"
YouTube comments can be noisy (spam, emojis, etc.). Our script looks for specific "Pain Point" keywords like *"stipend delay"*, *"no sleep"*, or *"senior ragging"*.
- If a comment is just "Nice video!", it is ignored.
- If a comment says "I also have 48-hour shifts and I'm crying," it is saved as a high-value lead.

### Step 5: Formatting for Supabase
The script takes these emotional comments and prepares them for the database:
- **User ID**: The person's YouTube handle.
- **Pain Point**: The text of their comment.
- **Source**: Labeled as `youtube_comment` so we know where it came from.
- **Created At**: Today's date (since YouTube relative dates like "2 months ago" are hard to pinpoint exactly without an API key).

---

### Note on Dependencies
Unlike the Reddit script which uses simple web requests, the YouTube script works best with a helper tool called `youtube-comment-downloader`. This tool handles the complex way YouTube loads comments so we don't have to worry about it!
