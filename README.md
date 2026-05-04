# Medical Pain Point Scraper Project

This project automates the extraction of challenges and frustrations experienced by the Indian medical community from various social platforms.

## Modules

### Reddit Scraper
Scrapes Indian medical subreddits for pain points.
- **Location**: `Reddit/`
- **Documentation**: [`Reddit/README.md`](Reddit/README.md)

### YouTube Scraper
Extracts emotional pain points from medical influencer comment sections.
- **Location**: `YouTube/`
- **Documentation**: [`YouTube/README.md`](YouTube/README.md)

### LinkedIn Scraper
Extracts formal discussions on systemic issues (e.g., clerical burden, burnout surveys) from professional profiles.
- **Location**: `LinkedIn/`
- **Documentation**: [`LinkedIn/README.md`](LinkedIn/README.md)

### Facebook Scraper
Scrapes public Facebook pages and groups for medical pain points using mbasic HTML parsing.
- **Location**: `Facebook/`
- **Documentation**: [`Facebook/README.md`](Facebook/README.md)

## Shared Utilities
- **Supabase Integration**: All modules generate JSON data formatted for the same Supabase `leads` table. Each module has its own `push_to_supabase.py` script to upload data.
