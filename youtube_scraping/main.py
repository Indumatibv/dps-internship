import json
import time
import random
import ollama

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys


# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------
QUESTIONS = [
    "biggest pain points for doctors daily routine",
    "what do nurses find most frustrating at work",
    "medical students study struggles tips",
]

VIDEOS_PER_QUERY = 3
MAX_TOTAL_VIDEOS = 10


# -------------------------------------------------------
# CHROME SETUP
# -------------------------------------------------------
def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Chrome(options=options)


# -------------------------------------------------------
# LLM CALL
# -------------------------------------------------------
def call_mistral(prompt):
    try:
        res = ollama.chat(
            model="mistral:latest",
            messages=[
                {"role": "system", "content": "Be precise."},
                {"role": "user", "content": prompt}
            ]
        )
        return res["message"]["content"]
    except:
        return ""


# -------------------------------------------------------
# CLEAN QUERIES
# -------------------------------------------------------
def clean_queries(queries):
    clean = []
    for q in queries:
        if isinstance(q, str):
            clean.append(q)
        elif isinstance(q, dict):
            for k in ["query", "text", "q"]:
                if k in q and isinstance(q[k], str):
                    clean.append(q[k])
                    break
    return list(set(clean))


# -------------------------------------------------------
# GENERATE QUERIES
# -------------------------------------------------------
def generate_queries(question):
    prompt = f"""
Generate 5 short YouTube search queries for:
"{question}"

Rules:
- max 4 words
- real experience style

Return JSON array only
"""
    try:
        text = call_mistral(prompt)
        text = text.replace("```", "")
        text = text[text.find("["):text.rfind("]")+1]
        return clean_queries(json.loads(text))
    except:
        return [question]


# -------------------------------------------------------
# SEARCH YOUTUBE (HUMAN STYLE)
# -------------------------------------------------------
def search_youtube(driver, query, limit=5):
    driver.get("https://www.youtube.com/")
    time.sleep(2)

    box = driver.find_element(By.NAME, "search_query")
    box.clear()

    for ch in query:
        box.send_keys(ch)
        time.sleep(random.uniform(0.05, 0.1))

    box.send_keys(Keys.RETURN)
    time.sleep(2)

    elements = driver.find_elements(By.ID, "video-title")

    results = []
    seen = set()

    for el in elements:
        href = el.get_attribute("href")
        title = el.get_attribute("title")

        if href and "watch?v=" in href:
            vid = href.split("watch?v=")[-1][:11]

            if vid not in seen:
                seen.add(vid)
                results.append({
                    "video_id": vid,
                    "title": title,
                    "url": href
                })

        if len(results) >= limit:
            break

    return results


# -------------------------------------------------------
# FETCH COMMENTS (STRUCTURED)
# -------------------------------------------------------
def fetch_comments(driver, url, video_title, max_comments=30):
    driver.get(url)
    time.sleep(3)

    driver.execute_script("window.scrollTo(0, 1000);")
    time.sleep(2)

    comments = []
    seen = set()

    for _ in range(8):
        items = driver.find_elements(By.CSS_SELECTOR, "#content-text")

        for el in items:
            text = el.text.strip()

            if text and len(text.split()) > 6 and text not in seen:
                seen.add(text)

                comments.append({
                    "user_id": "",  # can extend later
                    "comment": text,
                    "video_name": video_title
                })

                if len(comments) >= max_comments:
                    return comments

        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(2)

    return comments


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
driver = setup_driver()

final_results = []

for q in QUESTIONS:
    print("\n" + "="*60)
    print("📌", q)

    queries = generate_queries(q)
    print("📝 Queries:", queries)

    all_videos = []
    all_comments = []

    # Step 1: Collect videos
    for query in queries:
        if not isinstance(query, str):
            continue

        query = query + " vlog experience"
        print("🔍", query)

        vids = search_youtube(driver, query, VIDEOS_PER_QUERY)
        all_videos.extend(vids)

        if len(all_videos) >= MAX_TOTAL_VIDEOS:
            break

    print("📦 Videos collected:", len(all_videos))

    # Step 2: Collect comments
    for v in all_videos[:MAX_TOTAL_VIDEOS]:
        print("📥", v["title"])

        comments = fetch_comments(driver, v["url"], v["title"])

        for c in comments:
            final_results.append({
                "question": q,
                "user_id": c["user_id"],
                "comment": c["comment"],
                "video_name": c["video_name"]
            })

    print("💬 Comments collected:", len(final_results))


driver.quit()

# -------------------------------------------------------
# SAVE
# -------------------------------------------------------
with open("youtube_structured_output.json", "w") as f:
    json.dump(final_results, f, indent=2)

print("\n✅ DONE")