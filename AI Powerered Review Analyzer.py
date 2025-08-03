

"""

AI-Powered Review Analyzer – Step 1
Ingest reviews from Google Maps using the Google Places API.

This script fetches customer reviews for Sassy Mama Sweets and stores them in a CSV file
for future sentiment analysis, topic modeling, or database storage.
"""
import requests
import pandas as pd
from datetime import datetime

# === CONFIGURATION ===
API_KEY = "place_KEY_HERE"
PLACE_ID = "PLACE_id_HERE" # 🆔 Sassy Mama Sweets (Southington, CT) 
FIELDS = "name,rating,reviews,user_ratings_total"
# =======================

# 🛰️ Build the API request URL
url = (
    f"https://maps.googleapis.com/maps/api/place/details/json?"
    f"place_id={PLACE_ID}&fields={FIELDS}&key={API_KEY}"
)

# 🔄 Send the request to Google Places API
response = requests.get(url)

# 🧪 DEBUG: Print raw API response
print("📦 RAW JSON RESPONSE:")
print(response.json())


if response.status_code != 200:
    raise Exception(f"Request failed: {response.status_code} - {response.text}")

# 📦 Parse the API response
result = response.json().get("result", {})
reviews = result.get("reviews", [])

# 🧼 Convert raw reviews to a structured DataFrame
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

# 🧾 Preview and confirm
print(f"\n✅ Fetched {len(df_reviews)} reviews for: {result.get('name')}")
print(df_reviews.head())

# 💾 Save to CSV for future use
csv_file = "google_reviews_raw.csv"
df_reviews.to_csv(csv_file, index=False)
print(f"\n📁 Reviews saved to: {csv_file}")

import sqlite3

# === Step 2: Save to SQLite Database ===
DB_NAME = "review_data.db"
TABLE_NAME = "google_reviews"

# Connect to the database (creates the file if it doesn't exist)
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Create the table (if it doesn't exist already)
cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_name TEXT,
        rating INTEGER,
        review_text TEXT,
        review_time TEXT,
        relative_time TEXT
    );
""")

# Insert reviews into the table
for _, row in df_reviews.iterrows():
    cursor.execute(f"""
        INSERT INTO {TABLE_NAME} (author_name, rating, review_text, review_time, relative_time)
        VALUES (?, ?, ?, ?, ?)
    """, (
        row["author_name"],
        row["rating"],
        row["review_text"],
        row["review_time"].isoformat(),
        row["relative_time"]
    ))

# Save and close
conn.commit()
conn.close()

print(f"\n🗄️  Reviews saved to SQLite database: {DB_NAME} in table '{TABLE_NAME}'")


"""
AI-Powered Review Analyzer – Step 3
Analyze review sentiment, topics, and summary using GPT-4
and store structured insights in a SQLite database.

Author: Eileen Nieves-Melja
"""

import sqlite3
import openai
import pandas as pd
import time

# === CONFIGURATION ===
DB_NAME = "review_data.db"
INPUT_TABLE = "google_reviews"
OUTPUT_TABLE = "review_insights"
OPENAI_API_KEY = "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"
# 🔐 Replace with your actual API key
MODEL = "gpt-3.5-turbo"  # or "gpt-3.5-turbo" if you're on a budget like me
# =======================

openai.api_key = OPENAI_API_KEY

# Connect to database
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Create output table (if not exists)
cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {OUTPUT_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id INTEGER,
        sentiment TEXT,
        topics TEXT,
        summary TEXT,
        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(review_id) REFERENCES {INPUT_TABLE}(id)
    );
""")

# Load raw reviews
df = pd.read_sql(f"SELECT id, review_text FROM {INPUT_TABLE}", conn)

def analyze_review(text):
    """Send a review to GPT and return structured sentiment, topics, and summary"""
    prompt = f"""
    Analyze the following customer review:

    "{text}"

    Return a JSON object with:
    - sentiment: "Positive", "Neutral", or "Negative"
    - topics: a list of key themes (e.g., service, product, pricing, atmosphere)
    - summary: a 1-2 sentence summary of what the review is about
    """

    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{
                "role": "system", "content": "You are a helpful review analyst.",
            }, {
                "role": "user", "content": prompt,
            }],
            temperature=0.4,
        )
        output = response['choices'][0]['message']['content']
        return eval(output)  # assuming GPT returns a clean dict

    except Exception as e:
        print(f"❌ Error analyzing review: {e}")
        return None

    # Loop through and analyze each review


for _, row in df.iterrows():
    review_id = row["id"]
    text = row["review_text"]

    # Skip empty or short reviews
    if not text or len(text.strip()) < 5:
        continue

    # Check if this review is already in insights
    cursor.execute(f"SELECT 1 FROM {OUTPUT_TABLE} WHERE review_id = ?", (review_id,))
    if cursor.fetchone():
        continue  # already processed

    result = analyze_review(text)
    if result:
        sentiment = result.get("sentiment")
        topics = ", ".join(result.get("topics", []))
        summary = result.get("summary")

        cursor.execute(f"""
                    INSERT INTO {OUTPUT_TABLE} (review_id, sentiment, topics, summary)
                    VALUES (?, ?, ?, ?)
                """, (review_id, sentiment, topics, summary))
        conn.commit()
        print(f"✅ Review {review_id} analyzed and saved.")
        time.sleep(21)  # waits 21 seconds between each review

conn.close()
print("\n🎉 All reviews analyzed and saved to 'review_insights'.")

