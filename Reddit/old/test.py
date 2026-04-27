import requests
import json
import time
import math

headers_reddit = {"User-Agent": "MyRedditScraper/1.0 (by u/yourusername)"}

MEDICAL_SUBREDDITS = [
    "medicine", "medical", "doctors", "medicalschool",
    "nursing", "residency", "physicianassistant", "healthcareworkers",
    "AskDocs", "medicaladvice"
]

# -------------------------------------------------------
# Use local Mistral via Ollama to generate search queries
# -------------------------------------------------------
def generate_search_queries(question, n=5):
    """Ask local Mistral to generate N different Reddit search queries."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral:latest",
                "prompt": f"""Generate {n} different Reddit search queries to find posts about this concern:
"{question}"

Rules:
- Each query should be short (2-6 words), like how someone would actually type on Reddit search
- Vary the angle: symptoms, frustrations, advice, venting, questions
- Focus on finding REAL experiences, not definitions
- Return ONLY a JSON array of strings, no explanation, no markdown

Example output: ["doctors paperwork frustration", "physician admin burden", "EHR documentation pain", "doctor daily routine problems", "medical admin overload"]""",
                "stream": False
            }
        )

        print(f"  Ollama status: {response.status_code}")

        if response.status_code != 200:
            print(f"  Ollama error: {response.text}")
            return [question]

        raw = response.json()
        text = raw.get("response", "").strip()
        print(f"  Raw Mistral output: {text}")

        # Strip markdown fences if present
        text = text.replace("```json", "").replace("```", "").strip()

        # Extract JSON array if there's extra text around it
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            text = text[start:end]

        queries = json.loads(text)
        return queries[:n]

    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e} | raw: {text}")
        return [question]
    except Exception as e:
        print(f"  Unexpected error in generate_search_queries: {e}")
        return [question]


# -------------------------------------------------------
# Reddit search
# -------------------------------------------------------
def search_reddit(query, subreddits=None, limit=5):
    all_results = []

    if subreddits:
        for sr in subreddits:
            url = f"https://www.reddit.com/r/{sr}/search.json"
            params = {
                "q": query,
                "sort": "relevance",
                "limit": limit,
                "type": "link",
                "t": "all",
                "restrict_sr": 1
            }
            try:
                resp = requests.get(url, headers=headers_reddit, params=params)
                if resp.status_code != 200:
                    continue
                for child in resp.json()["data"]["children"]:
                    d = child["data"]
                    all_results.append({
                        "title":        d["title"],
                        "post_id":      d["id"],
                        "subreddit":    d["subreddit"],
                        "score":        d["score"],
                        "num_comments": d["num_comments"],
                        "upvote_ratio": d.get("upvote_ratio", 0.5),
                    })
            except Exception as e:
                print(f"  Search error for r/{sr}: {e}")
            time.sleep(0.4)
    else:
        url = "https://www.reddit.com/search.json"
        params = {
            "q": query,
            "sort": "relevance",
            "limit": limit,
            "type": "link",
            "t": "all"
        }
        try:
            resp = requests.get(url, headers=headers_reddit, params=params)
            if resp.status_code == 200:
                for child in resp.json()["data"]["children"]:
                    d = child["data"]
                    all_results.append({
                        "title":        d["title"],
                        "post_id":      d["id"],
                        "subreddit":    d["subreddit"],
                        "score":        d["score"],
                        "num_comments": d["num_comments"],
                        "upvote_ratio": d.get("upvote_ratio", 0.5),
                    })
        except Exception as e:
            print(f"  Global search error: {e}")

    return all_results


# -------------------------------------------------------
# Pick best post from candidates
# -------------------------------------------------------
def pick_best_post(results, used_post_ids, min_comments=2):
    seen = set()
    unique = []
    for r in results:
        if r["post_id"] not in seen and r["post_id"] not in used_post_ids:
            seen.add(r["post_id"])
            unique.append(r)

    filtered = [r for r in unique if r["num_comments"] >= min_comments]
    if not filtered:
        filtered = unique
    if not filtered:
        return None

    def relevance_score(p):
        capped = min(p["num_comments"], 500)
        return p["upvote_ratio"] * math.log(capped + 1, 10)

    return max(filtered, key=relevance_score)


# -------------------------------------------------------
# Fetch lazy-loaded replies
# -------------------------------------------------------
def fetch_replies_for(subreddit, post_id, comment_id):
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/_/{comment_id}.json?limit=5"
    try:
        resp = requests.get(url, headers=headers_reddit)
        if resp.status_code != 200:
            return []
        data = resp.json()
        if len(data) < 2:
            return []
        children = data[1]["data"]["children"]
        if children and children[0].get("kind") == "t1":
            top = children[0]["data"]
            replies = top.get("replies", "")
            if replies and isinstance(replies, dict):
                return replies["data"]["children"]
    except Exception as e:
        print(f"  fetch_replies_for error: {e}")
    return []


# -------------------------------------------------------
# Recursively extract comments
# -------------------------------------------------------
def extract_comments(comment_node, subreddit, post_id, depth=0, max_depth=5):
    if comment_node.get("kind") == "more":
        return []
    if comment_node.get("kind") != "t1":
        return []

    cdata = comment_node["data"]
    body = cdata.get("body", "")

    if body in ("[deleted]", "[removed]", ""):
        return []
    if cdata.get("distinguished") == "moderator":
        return []

    comment = {
        "depth":   depth,
        "author":  cdata.get("author", "[deleted]"),
        "body":    body,
        "score":   cdata.get("score", 0),
        "replies": []
    }

    if depth >= max_depth:
        return [comment]

    raw_replies = cdata.get("replies", "")
    if raw_replies and isinstance(raw_replies, dict):
        reply_children = raw_replies["data"]["children"]
    elif raw_replies == "":
        reply_children = fetch_replies_for(subreddit, post_id, cdata["id"])
    else:
        reply_children = []

    nested_count = 0
    for reply in reply_children:
        if nested_count >= 5:
            break
        if reply.get("kind") == "t1":
            nested = extract_comments(reply, subreddit, post_id, depth + 1, max_depth)
            if nested:
                comment["replies"].extend(nested)
                nested_count += 1

    return [comment]


# -------------------------------------------------------
# Scrape a full post + comments
# -------------------------------------------------------
def scrape_post(post_id, subreddit, max_top_comments=10, max_depth=5):
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?limit={max_top_comments}"
    try:
        resp = requests.get(url, headers=headers_reddit)
        if resp.status_code != 200:
            print(f"  scrape_post failed: status {resp.status_code}")
            return None

        data = resp.json()
        post = data[0]["data"]["children"][0]["data"]
        all_comments = []

        for item in data[1]["data"]["children"]:
            if len(all_comments) >= max_top_comments:
                break
            if item.get("kind") == "t1":
                extracted = extract_comments(item, subreddit, post_id, depth=0, max_depth=max_depth)
                all_comments.extend(extracted)

        return {
            "question":    post["title"],
            "explanation": post["selftext"],
            "post_id":     post_id,
            "subreddit":   subreddit,
            "url":         f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/",
            "comments":    all_comments
        }
    except Exception as e:
        print(f"  scrape_post error: {e}")
        return None


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
QUESTIONS = [
    "biggest pain points for doctors daily routine",
    "what do nurses find most frustrating at work",
    "medical students study struggles tips",
]

all_results = []
used_post_ids = set()

for q in QUESTIONS:
    print(f"\n{'='*60}")
    print(f"📌 Question: {q}")

    # Step 1: Generate multiple search query variations via Mistral
    print(f"  🤖 Generating search query variations...")
    queries = generate_search_queries(q, n=5)
    print(f"  📝 Queries: {queries}")

    # Step 2: Run ALL queries and pool all candidates
    all_candidates = []
    for query in queries:
        print(f"  🔍 Searching: '{query}'")
        results = search_reddit(query, subreddits=MEDICAL_SUBREDDITS, limit=5)

        # Fallback to global Reddit if subreddit search returned nothing
        if not results:
            results = search_reddit(query, subreddits=None, limit=5)

        all_candidates.extend(results)
        time.sleep(0.5)

    print(f"  📦 Total candidates pooled: {len(all_candidates)}")

    # Step 3: Pick the single best unique post from the full pool
    best = pick_best_post(all_candidates, used_post_ids)

    if not best:
        print("  ❌ No suitable post found.")
        continue

    print(f"  ✅ Best match: [r/{best['subreddit']}] {best['title'][:80]}")
    print(f"     💬 {best['num_comments']} comments | ⬆️  score: {best['score']}")

    used_post_ids.add(best["post_id"])
    time.sleep(1)

    # Step 4: Scrape the post
    scraped = scrape_post(best["post_id"], best["subreddit"])
    if scraped:
        scraped["search_query"] = q
        scraped["queries_tried"] = queries
        all_results.append(scraped)
        print(f"  📥 Scraped {len(scraped['comments'])} top-level comments")

    time.sleep(1.5)

# Save output
with open("reddit_results.json", "w") as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

print(f"\n✅ Done! {len(all_results)} posts saved to reddit_results.json")