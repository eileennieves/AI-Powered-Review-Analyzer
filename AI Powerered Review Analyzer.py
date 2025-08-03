"""
AI-Powered Review Analyzer
Ingests Google Maps reviews and uses GPT to extract sentiment, topics, and summaries.

Author: Eileen Nieves-Melja
"""

# === IMPORTS ===
import requests
import pandas as pd
import sqlite3
import openai
import time
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# === ENVIRONMENT VARIABLES ===
load_dotenv()  # Make sure you have a .env file with your API keys

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === CONFIGURATION ===
PLACE_ID = "your-google-place-id-here"  # Example: "ChIJ2ZiapDW354kRBHjHUvTnMJo"
FIELDS = "name,rating,reviews,user_ratings_total"
DB_NAME = "review_data.db"
RAW_TABLE = "google_reviews"
INSIGHT_TABLE = "review_insights"
GPT_MODEL = "gpt-3.5-turbo"  # or "gpt-4" if available
# =======================

# === STEP 1: Fetch Reviews ===
print("\n📥 Fetching reviews from Google Places API...")
url = (
    f"https://maps.googleapis.com/maps/api/place/details/json?"
    f"place_id={PLACE_ID}&fields={FIELDS}&key={GOOGLE_API_KEY}"
)
response = requests.get(url)
print("📦 RAW JSON RESPONSE:")
print(response.json())

if response.status_code != 200:
    raise Exception(f"Request failed: {response.status_code} - {response.text}")

result = response.json().get("result", {})
reviews = result.get("reviews", [])

df_reviews = pd.DataFrame([
    {
        "author_name": r.get("author_name"),
        "rating": r.get("rating"),
        "review_text": r.get("text"),
        "review_time": datetime.fromtimestamp(r.get("time")),
        "relative_time": r.get("relative_time_description"),
    }
    for r in reviews
])

print(f"\n✅ Fetched {len(df_reviews)} reviews for: {result.get('name')}")
print(df_reviews.head())

# Save to CSV
csv_file = "google_reviews_raw.csv"
df_reviews.to_csv(csv_file, index=False)
print(f"\n💾 Reviews saved to CSV: {csv_file}")

# === STEP 2: Save to SQLite Database ===
print("\n🧱 Saving raw reviews to database...")
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {RAW_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_name TEXT,
        rating INTEGER,
        review_text TEXT,
        review_time TEXT,
        relative_time TEXT
    );
""")

for _, row in df_reviews.iterrows():
    cursor.execute(f"""
        INSERT INTO {RAW_TABLE} (author_name, rating, review_text, review_time, relative_time)
        VALUES (?, ?, ?, ?, ?)
    """, (
        row["author_name"],
        row["rating"],
        row["review_text"],
        row["review_time"].isoformat(),
        row["relative_time"]
    ))

conn.commit()
print(f"✅ Reviews saved to table '{RAW_TABLE}' in database '{DB_NAME}'")

# === STEP 3: Analyze Reviews with GPT ===
print("\n🧠 Starting GPT review analysis...")
openai.api_key = OPENAI_API_KEY

cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {INSIGHT_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id INTEGER,
        sentiment TEXT,
        topics TEXT,
        summary TEXT,
        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(review_id) REFERENCES {RAW_TABLE}(id)
    );
""")

df = pd.read_sql(f"SELECT id, review_text FROM {RAW_TABLE}", conn)

def analyze_review(text):
    """Uses GPT to analyze review sentiment, topics, and summary"""
    prompt = f"""
    Analyze the following customer review:

    "{text}"

    Return a JSON object with:
    {{
        "sentiment": "Positive" | "Neutral" | "Negative",
        "topics": ["..."],
        "summary": "..."
    }}
    """

    try:
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful review analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
        )
        output = response['choices'][0]['message']['content']
        return json.loads(output)  # Safer than eval()

    except Exception as e:
        print(f"❌ Error analyzing review: {e}")
        return None

# Loop through reviews
for _, row in df.iterrows():
    review_id = row["id"]
    text = row["review_text"]

    if not text or len(text.strip()) < 5:
        continue

    # Skip if already analyzed
    cursor.execute(f"SELECT 1 FROM {INSIGHT_TABLE} WHERE review_id = ?", (review_id,))
    if cursor.fetchone():
        continue

    result = analyze_review(text)
    if result:
        sentiment = result.get("sentiment")
        topics = ", ".join(result.get("topics", []))
        summary = result.get("summary")

        cursor.execute(f"""
            INSERT INTO {INSIGHT_TABLE} (review_id, sentiment, topics, summary)
            VALUES (?, ?, ?, ?)
        """, (review_id, sentiment, topics, summary))
        conn.commit()
        print(f"✅ Review {review_id} analyzed and saved.")
        time.sleep(20)  # Avoid rate limit

conn.close()
print("\n🎉 All reviews analyzed and saved to 'review_insights'.")
