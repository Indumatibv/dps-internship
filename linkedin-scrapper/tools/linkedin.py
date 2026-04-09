import re
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from typing import Optional

# Global browser instance initialized by the agent
_browser_manager = None

def init_tools(browser_manager):
    global _browser_manager
    _browser_manager = browser_manager

@tool
async def scrape_profile(url: str) -> str:
    """Visits a LinkedIn profile URL and extracts the textual information (experience, education, about)."""
    if not _browser_manager:
        return "Browser not initialized."
    
    await _browser_manager.navigate(url)
    await _browser_manager.human_delay(3, 6)
    
    # Scroll a bit to load lazy elements
    for _ in range(3):
        await _browser_manager.scroll_down()
        
    html = await _browser_manager.get_html()
    soup = BeautifulSoup(html, "html.parser")
    
    # Extract text from main sections
    main_main = soup.find("main")
    if not main_main:
        return "Could not find main element. We might be on a login page or the layout changed."
    
    sections = []
    
    # Try to extract structured sections
    for section in main_main.find_all("section"):
        header = section.find(["h2", "h3"])
        header_text = header.get_text(strip=True) if header else "Section"
        body_text = section.get_text(separator='\n', strip=True)
        body_text = re.sub(r'\n+', '\n', body_text)
        if len(body_text) > 20:  # Skip tiny empty sections
            sections.append(f"### {header_text}\n{body_text}")
    
    if sections:
        result = '\n\n'.join(sections)
    else:
        text = main_main.get_text(separator='\n', strip=True)
        text = re.sub(r'\n+', '\n', text)
        result = text
    
    return f"Profile Data from {url}:\n{result[:8000]}"

@tool
async def search_linkedin(query: str) -> str:
    """Searches LinkedIn for users, jobs, or companies using a search query."""
    if not _browser_manager:
        return "Browser not initialized."
        
    encoded_query = query.replace(' ', '%20')
    search_url = f"https://www.linkedin.com/search/results/all/?keywords={encoded_query}"
    
    await _browser_manager.navigate(search_url)
    await _browser_manager.human_delay(3, 5)
    
    # Scroll multiple times to load more results  
    for _ in range(3):
        await _browser_manager.scroll_down()
    
    html = await _browser_manager.get_html()
    soup = BeautifulSoup(html, "html.parser")
    
    results = []
    
    # Extract individual search result cards
    result_cards = soup.find_all("div", class_=re.compile(r"entity-result"))
    if not result_cards:
        result_cards = soup.find_all("li", class_=re.compile(r"reusable-search"))
    
    for i, card in enumerate(result_cards[:15]):  # Cap at 15 results
        # Extract title/name
        title_el = card.find("span", class_=re.compile(r"entity-result__title"))
        if not title_el:
            title_el = card.find(["h3", "span"], class_=re.compile(r"title"))
        
        # Extract subtitle (headline, company, etc.)
        subtitle_el = card.find("div", class_=re.compile(r"entity-result__primary-subtitle"))
        if not subtitle_el:
            subtitle_el = card.find("p", class_=re.compile(r"subline"))
        
        # Extract summary/snippet text
        summary_el = card.find("p", class_=re.compile(r"entity-result__summary"))
        if not summary_el:
            summary_el = card.find("div", class_=re.compile(r"summary"))
        
        # Extract location
        location_el = card.find("div", class_=re.compile(r"entity-result__secondary-subtitle"))

        # Build the result entry
        title = title_el.get_text(strip=True) if title_el else None
        subtitle = subtitle_el.get_text(strip=True) if subtitle_el else None
        summary = summary_el.get_text(strip=True) if summary_el else None
        location = location_el.get_text(strip=True) if location_el else None
        
        # Extract any URLs
        link_el = card.find("a", href=re.compile(r"linkedin.com"))
        link = link_el["href"] if link_el and link_el.get("href") else None
        
        if title:
            entry = f"{i+1}. **{title}**"
            if subtitle: entry += f"\n   Role: {subtitle}"
            if location: entry += f"\n   Location: {location}"
            if summary: entry += f"\n   Summary: {summary}"
            if link: entry += f"\n   URL: {link}"
            results.append(entry)
    
    if results:
        return f"Search Results for '{query}' ({len(results)} results):\n\n" + "\n\n".join(results)
    
    # Fallback: get all text from results container
    search_container = soup.find("div", {"class": "search-results-container"})
    if not search_container:
        search_container = soup.find("main")
        
    if not search_container:
        return "Could not extract search results. Layout may have changed."
    
    # Even in fallback, try to extract cleaner text
    # Remove navigation, buttons, and other noise
    for tag in search_container.find_all(["nav", "button", "header", "footer", "script", "style"]):
        tag.decompose()
    
    text = search_container.get_text(separator='\n', strip=True)
    text = re.sub(r'\n+', '\n', text)
    # Remove very short lines (likely UI artifacts)
    lines = [l for l in text.split('\n') if len(l.strip()) > 15]
    text = '\n'.join(lines)
    
    return f"Search Results for '{query}':\n{text[:8000]}"
