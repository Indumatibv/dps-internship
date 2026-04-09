import json
import ollama
import time


# -------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------
with open("youtube_structured_output.json", "r") as f:
    data = json.load(f)


# -------------------------------------------------------
# LLM CALL
# -------------------------------------------------------
def call_mistral(prompt):
    try:
        res = ollama.chat(
            model="mistral:latest",
            messages=[
                {"role": "system", "content": "Be strict and precise."},
                {"role": "user", "content": prompt}
            ]
        )
        return res["message"]["content"]
    except:
        return ""


# -------------------------------------------------------
# RELEVANCE CHECK (CORE)
# -------------------------------------------------------
def is_relevant(question, comment):
    prompt = f"""
Question:
{question}

Comment:
{comment}

Is this comment useful for answering the question?

Rules:
- YES → if it contains real experience, struggle, advice, or opinion
- NO → if it is joke, spam, compliment, irrelevant

Answer ONLY: YES or NO
"""

    result = call_mistral(prompt).strip().upper()
    return "YES" in result


# -------------------------------------------------------
# FILTER LOOP
# -------------------------------------------------------
filtered = []

for i, item in enumerate(data):
    q = item["question"]
    comment = item["comment"]

    print(f"🔎 Checking {i+1}/{len(data)}")

    try:
        if is_relevant(q, comment):
            filtered.append(item)
    except:
        continue

    time.sleep(0.3)  # avoid overload


# -------------------------------------------------------
# SAVE OUTPUT
# -------------------------------------------------------
with open("youtube_filtered.json", "w") as f:
    json.dump(filtered, f, indent=2)

print("\n✅ DONE")
print(f"Kept {len(filtered)} out of {len(data)} comments")