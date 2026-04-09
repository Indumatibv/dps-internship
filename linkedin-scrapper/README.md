# LinkedIn Scraping Agent

This is an LLM-powered agent designed to navigate and scrape LinkedIn. It uses [Playwright](https://playwright.dev/python/) for browser automation, [LangChain & LangGraph](https://python.langchain.com/) for agent orchestration, and [Mistral](https://mistral.ai/) for decision making.

## Prerequisites
- Python 3.10+
- Chrome/Chromium
- Mistral API Key

## Setup

1. **Clone/Navigate to the repository**
2. **Create and activate the virtual environment (if not already done)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
4. **Environment Variables**
   Copy `.env.example` to `.env` and fill in your Mistral API Key and optionally your LinkedIn Credentials:
   ```bash
   cp .env.example .env
   # Edit .env and add your MISTRAL_API_KEY
   # Optinally add LINKEDIN_USERNAME and LINKEDIN_PASSWORD
   ```

## Authentication (CRITICAL)

LinkedIn aggressively blocks automated logins. We provide two ways to log in:

**Method 1: Auto-Login & Interactive Console (Recommended)**
1. Provide your `LINKEDIN_USERNAME` and `LINKEDIN_PASSWORD` in `.env`.
2. When the script runs, it will attempt to type them in. If LinkedIn detects a new login and asks for a CAPTCHA or 2FA, simply solve it in the popup browser window!
3. The script will wait for you to reach the feed and then automatically save your session to `cookies.json`.

**Method 2: Cookie Export Extension**
1. Log into your real LinkedIn account using your normal browser (e.g., Chrome).
2. Install a browser extension like **EditThisCookie** or **Cookie-Editor**.
3. While on `linkedin.com`, use the extension to "Export" your cookies in JSON format.
4. Paste the JSON into a file named `cookies.json` in the root of this project.

## Usage

Simply run the `main.py` script:

```bash
python3 main.py
```

The agent will launch a non-headless browser window so you can observe its actions. Once initialized, it will give you a prompt to enter a query.

Example Queries:
- *Search for "Software Engineer" on LinkedIn and tell me what you find.*
- *Check out this profile: https://www.linkedin.com/in/some-user/ and give me a summary of their experience.*
- *Look for jobs related to "Python Developer" in "New York" and extract the first 3 listings.*

## Known Limitations & Anti-Bot Measures
- The browser runs with `headless=False` to reduce the chance of bot detection.
- Human-like delays (3-6 seconds) and scrolling are implemented before extraction.
- **Do not run this excessively** or LinkedIn may temporarily restrict your account. Keep the query volume low.
