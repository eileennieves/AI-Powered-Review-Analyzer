# 🧠 AI-Powered Google Review Analyzer

This project uses Python, the Google Places API, and OpenAI's GPT models to fetch and analyze public Google Reviews. It extracts meaningful business insights such as sentiment, key themes, and concise summaries, storing the results in a structured SQLite database.

---

## 🚀 Features

- ✅ Pulls reviews directly from Google Maps via the Places API
- 🧹 Cleans and structures the raw review data using `pandas`
- 🤖 Uses GPT-4 or GPT-3.5 Turbo for AI-powered sentiment analysis and topic extraction
- 💾 Stores both raw and analyzed reviews in a local SQLite database
- 📊 Easily extendable for dashboards, reports, or customer experience feedback loops

---

## 🛠️ Technologies Used

- Python 3.x
- SQLite (built-in)
- Google Maps Places API
- OpenAI GPT-4 / GPT-3.5 Turbo
- `pandas`, `requests`, `openai`, `time`

---

## 📦 How It Works

### **Step 1: Fetch Reviews**
- Uses the Google Places API to retrieve reviews using your business's Place ID.
- Data includes reviewer name, rating, text, timestamp, and more.

### **Step 2: Save + Structure**
- Reviews are saved to a `google_reviews_raw.csv` file.
- Also stored in a SQLite database (`review_data.db`) for querying and analysis.

### **Step 3: AI-Powered Analysis**
- Each review is analyzed by GPT-4 (or 3.5) for:
  - Sentiment (`Positive`, `Neutral`, `Negative`)
  - Key topics (`service`, `product`, `pricing`, etc.)
  - A short summary
- Results are saved in a second database table (`review_insights`).

---

## 🔑 API Keys

To run this project, you’ll need:

- A [Google Places API key](https://console.cloud.google.com/apis/library/places-backend.googleapis.com)
- An [OpenAI API key](https://platform.openai.com/account/api-keys)

Replace the placeholders in the script with your actual API keys:

```python
API_KEY = "your-google-api-key"
OPENAI_API_KEY = "your-openai-api-key"
```
---

## 📊 Example Output Table

| Review Text                                | Sentiment | Topics           | Summary                                        |
|--------------------------------------------|-----------|------------------|------------------------------------------------|
| "Amazing cake and great service!"          | Positive  | cake, service    | A happy customer enjoyed the cake and service. |

---

## 💡 Future Ideas

- Add a Streamlit or Flask dashboard to explore review insights
- Automatically generate weekly summary reports
- Integrate with Power BI or Google Data Studio
- Add multilingual sentiment support using translation

---

## 👩‍💻 Author

**Eileen Nieves-Melja**  
📫 [LinkedIn](https://www.linkedin.com/in/eileen-nieves)  
📁 [GitHub Portfolio](https://github.com/eileennieves)

---

> ✨ This project was built to support local small businesses and showcase real-world AI + data engineering skills.
