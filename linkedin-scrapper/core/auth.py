import json
import os
from pathlib import Path

def load_cookies(filepath='cookies.json'):
    """Loads cookies from a JSON file."""
    cookie_path = Path(filepath)
    if not cookie_path.exists():
        print(f"Cookie file {filepath} not found. You need to export cookies from your browser.")
        return []
    
    with open(cookie_path, 'r') as f:
        cookies = json.load(f)
    return cookies

def save_cookies(cookies, filepath='cookies.json'):
    """Saves cookies to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(cookies, f, indent=4)
    print(f"Cookies saved to {filepath}")

async def perform_auto_login(browser_manager, username, password, cookies_path='cookies.json'):
    """Attempts to auto-login to LinkedIn using Playwright."""
    page = browser_manager.page
    print("Attempting automatic login...")
    await page.goto("https://www.linkedin.com/login")
    
    try:
        await page.wait_for_selector("#username", timeout=5000)
        await page.fill("#username", username)
        await browser_manager.human_delay(1, 2)
        await page.fill("#password", password)
        await browser_manager.human_delay(1, 2)
        await page.click("button[type='submit']")
        
        print("\nLogin submitted! Waiting to see if verification/captcha is required...")
        print("Note: If you see a CAPTCHA or 2FA, please solve it manually in the browser window.")
        
        # Wait up to 60 seconds for the user to solve captcha OR for the feed to load
        await page.wait_for_url("**/feed/**", timeout=60000)
        print("Successfully reached the feed! Saving cookies...")
        
        cookies = await browser_manager.get_cookies()
        save_cookies(cookies, cookies_path)
    except Exception as e:
        print("\nLogin automatic flow couldn't complete. You might need to manually verify.")
        input("Please solve any login challenges in the browser window, then press Enter here once you are on the feed...")
        if "feed" in page.url or "linkedin.com/in/" in page.url:
            print("Detected active session. Saving cookies...")
            cookies = await browser_manager.get_cookies()
            save_cookies(cookies, cookies_path)
        else:
            print("Failed to detect successful login.")
