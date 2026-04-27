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
