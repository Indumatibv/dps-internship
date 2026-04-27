Ran command: `python YouTube/scrape_youtube_med.py`

For YouTube, we used a **Hybrid Scraping approach** that doesn't require an official API key. Here is the breakdown:

### 1. Discovery (Search & Regex)
First, the script uses the standard `requests` library to "search" YouTube for the channels and keywords you provided. Instead of using a complex API, it uses **Regular Expressions (Regex)** to find the unique 11-character Video IDs (like `ePq8lqBkock`) directly from the search result page's code.

### 2. Extraction (AJAX Simulation)
To get the comments, we used a specialized library called `youtube-comment-downloader`. 
*   **The Challenge**: YouTube doesn't just put comments in the HTML; it loads them dynamically as you scroll using complex background requests (AJAX).
*   **The Solution**: This library simulates those background requests to "trick" YouTube into sending the comment data in JSON format, which we then download. This is much faster and more reliable than trying to "read" the visual webpage.

### 3. Filtering (Keyword Matching)
Once we have the raw comments, we apply the same **Keyword Filter** logic we used for Reddit. The script reads every comment and only saves it as a "lead" if it contains words like *"stipend"*, *"ragging"*, *"burnout"*, or *"duty hours"*.

### 4. Safety & Throttling
*   **Limits**: As you noticed, I limited it to the top **20 videos** to prevent your IP from being temporarily blocked by YouTube.
*   **Delays**: The script waits 3 seconds between videos to look more like a human and less like a bot.

**In short: We used "Search Scraping" to find videos and "AJAX Simulation" to grab the comments, all without needing a Google API Key!**

---------------------------------------
# YouTube Medical Pain Point Scraper

This script extracts emotional and experience-based comments from YouTube videos related to the Indian medical community. It treats comment sections as "digital focus groups" to find real-world frustrations.

## Features

- **Targeted Channels**: Scans top medical influencers like `@DrAnujPachhel`, `@mitali.this.side`, and others.
- **Search Discovery**: Finds videos using specific queries like *"First 24-hour internship duty vlog"* and *"NEET PG hell week"*.
- **Comment Extraction**: Uses `youtube-comment-downloader` to bypass the need for an official API key.
- **Pain Point Filtering**: Only saves comments that contain keywords related to burnout, toxic culture, or clinical struggles.
- **Supabase Ready**: Outputs JSON data ready for the `leads` table with `source='youtube_comment'`.

## Setup

1. Install dependencies:
   ```bash
   pip install -r YouTube/requirements.txt
   ```

2. Run the scraper:
   ```bash
   python YouTube/scrape_youtube_med.py
   ```

## Output

- `YouTube/scraped_youtube_leads.json`: Full data including video URLs and like counts.
- `YouTube/scraped_youtube_leads_supabase_ready.json`: Clean data for database ingestion.

## Note on Methodology
The script first identifies relevant videos by searching for target channels and queries. It then iterates through these videos and downloads their most recent comments, filtering them for specific "pain point" keywords to ensure high-quality leads.
