# Medical Pain Point Scraper

This project is designed to scrape medical-related subreddits (specifically focused on the Indian medical community) to identify and extract "pain points" from posts and comments. The goal is to gather insights into the challenges faced by medical students, interns, and residents.

## Features

- **Targeted Scraping**: Focuses on subreddits like `r/IndianMedSchool`, `r/MBBSindia`, `r/Residency`, etc.
- **Pain Point Detection**: Uses a keyword-based approach to identify relevant frustrations, bureaucratic hurdles, and workload issues.
- **Lead Generation**: Formats the scraped data to match a Supabase `leads` table schema for future integration.
- **JSON Storage**: Saves results locally in `scraped_leads.json` for review before database ingestion.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the scraper:
   ```bash
   python3 Reddit/scrape_indian_med.py
   ```

## Data Schema

The scraped data is formatted as follows:

| Field | Description |
|-------|-------------|
| `user_id` | Reddit username |
| `pain_point` | The content of the post or comment |
| `email` | Null (placeholder for future use) |
| `phone` | Null (placeholder for future use) |
| `source` | URL of the Reddit post/comment |
| `created_at` | Timestamp of the original post |
| `processed` | Boolean flag (default: false) |

## Future Work

- **Supabase Integration**: A script to push the `scraped_leads.json` data to a Supabase database.
- **LLM Refinement**: Use a local LLM (like Mistral via Ollama) to better categorize and summarize pain points.
