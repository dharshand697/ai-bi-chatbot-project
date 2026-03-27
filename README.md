# AI BI Chatbot Project

This repository contains the **Team 1 – Data Engineering Module** of an AI-powered Conversational Business Intelligence system.

---

## 📌 Project Objective

To prepare a clean, analytics-ready master dataset that enables downstream teams (NLP, Analytics Engine, Visualization, Chatbot Integration) to build a conversational BI assistant.

---

## 🏗 Project Structure
---------------------------------------------------------------------------------------------
ai-bi-chatbot-project/
├── data/
│ ├── raw/
│ └── processed/
│ └── master_dataset.csv
├── reports/
│ ├── data_dictionary.xlsx
│ ├── 1_monthly_revenue.png
│ ├── 2_quarterly_revenue.png
│ └── ...
├── scripts/
│ ├── data_cleaning.py
│ ├── feature_engineering.py
│ ├── data_merging.py
│ ├── run_pipeline.py
│ └── eda_analysis.py
├── requirements.txt
└── README.md
-----------------------------------------------------------------------------------------------------

---

## ✅ Team 1 Deliverables

- Cleaned and standardized raw datasets
- Feature engineered time variables
- Generated analytics-ready master dataset
- Created 7 professional EDA charts
- Prepared Data Dictionary
- Uploaded structured project to GitHub

---

## 🚀 How to Run the Project

### 1️⃣ Clone Repository
---------------------------------------------------------------------------------------------
git clone https://github.com/dharshand697/ai-bi-chatbot-project.git

cd ai-bi-chatbot-project

### 2️⃣ Install Requirements
pip install -r requirements.txt

### 3️⃣ Run Data Pipeline
python scripts/run_pipeline.py
--------------------------------------------------------------------------------------------

## 📊 Key Dataset Fields (For NLP Team)

| Field | Description |
|-------|------------|
| sales | Revenue metric |
| month_id | Month of order |
| qtr_id | Quarter of order |
| year_id | Year of order |
| productline | Product category |
| country | Customer country |
| dealsize | Deal size category |
| customername | Customer name |
----------------------------------------------------------------------------------------
## 📌 Repository Link

https://github.com/dharshand697/ai-bi-chatbot-project
Team 1 – Data Engineering


---

## Team 2 - NLP Intent Recognition

### Module Overview
Classifies user queries into one of 5 intents so the analytics
engine knows which analysis to run.

### Files Added
- `nlp/training_data.py` - 160 labelled training queries across 5 intents
- `nlp/intent_classifier.py` - TF-IDF vectorizer and classifier training

### Intents Supported
| Intent | Example Query |
|---|---|
| sales_query | "What is total revenue in Q3?" |
| ranking_query | "Top 5 countries by revenue" |
| comparison_query | "Compare 2003 vs 2004 sales" |
| forecast_query | "Predict next month revenue" |
| hr_query | "What is the attrition rate?" |

### How to Run
    python Team2_module/intent_classifier.py
### how to run test file
    python Team2_module/test_interactive.py

### Output
- `models/intent_model.pkl` - trained classifier
- `models/vectorizer.pkl` - fitted TF-IDF vectorizer
- `reports/intent_accuracy.txt` - accuracy report

### Dependencies
- scikit-learn

### UPDATED NLP MODULE CONSISTS OF 
🔧 Additional Files Added
entity_extractor.py – Extracts entities (numbers, metrics, time, filters)
query_builder.py – Converts intent + entities into structured query
analytics_client.py – Sends structured query to FastAPI /analyze endpoint
response_generator.py – Converts API response into human-readable output

⚡ New Capabilities
Entity extraction:
Numbers (e.g., Top 5 → top_n = 5)
Metrics (revenue → sales mapping)
Time filters (last month, this month)
Basic filters (region, category, product)
Structured query generation:
Converts natural language → backend-ready JSON
API integration:
Connects NLP module with analytics engine via REST API
Response generation:
Formats results into readable answers

🔗 Integration Update

NLP module now connects with analytics backend:

NLP → Structured Query → FastAPI (/analyze) → Analytics Engine → Response
🧪 Debug Mode (New)

### Interactive tester now includes NLP debugging:

Displays extracted entities
Shows structured query
Prints API response
⚠️ Additional Requirements
FastAPI backend must be running:
python -m uvicorn main:app --reload
OPEN ANOTHER TERMINAL and run the nlp module 

## Team 3 - Analytics Engine

### project structure

├── analytics_engine/ ← YOUR MODULE 
│ 
│ ├── core/ 
│ │ ├── engine.py ← Main controller 
│ │ ├── query_validator.py 
│ ├── forecasting/ 
│ │ ├── forecast_engine.py 
│ ├── insights/ 
│ │ ├── insight_generator.py 
│ │ ├── growth_kpi.py 
│ ├── kpi/ 
│ │ ├── growth_kpi.py 
│ │ ├── revenue_kpi.py 
│ ├── processors/ 
│ │ ├── filter_processor.py 
│ │ ├── groupby_processor.py 
│ │ ├── ranking_processor.py 
│ ├── utils/ 
│ │ ├── metric_mapper.py 
│ │ ├── response_formatter.py 
│ └── config.py 
│─ api/ 
│ ├── main.py ← FastAPI entry point 
--
### overview of each function

🔹 core/

engine.py: Orchestrates the full pipeline — takes parsed query → validates → routes to processors/KPIs/forecast → returns final response.

query_validator.py: Ensures the query is valid (correct metric, aggregation, filters) before execution.

🔹 forecasting/

forecast_engine.py: Generates future predictions (e.g., sales trends) using time-series or ML models.

🔹 insights/

insight_generator.py: Converts raw numbers into human-readable insights (e.g., “Sales increased by 20%”).

growth_kpi.py: Computes growth-related insights like MoM/YoY percentage changes.

🔹 kpi/

growth_kpi.py: Calculates growth metrics (rate of change, trends).

revenue_kpi.py: Computes revenue-based KPIs like total revenue, average revenue, etc.

🔹 processors/

filter_processor.py: Applies conditions (e.g., region = “India”, year = 2023).

groupby_processor.py: Groups data (e.g., sales by region/category).

ranking_processor.py: Produces ranked outputs (e.g., top 5 products by sales).

🔹 utils/

metric_mapper.py: Maps user-friendly terms (“sales”) to dataset column names.

response_formatter.py: Formats output into structured API response (JSON).

🔹 config.py

Stores constants like supported metrics, aggregations, column mappings.

🔹 api/

main.py: Exposes the analytics engine via FastAPI endpoints for external use.

### INTEGRATED WITH NLP MODULE SUCCESSFULLY

### to run the code 
python -m uvicorn api.main:app --reload

## Team 4 - Visualization & Dashboard Module

### 📊 Module Overview

The Visualization module provides an interactive dashboard to display insights generated by the analytics engine. It integrates outputs from Team 1 (data), Team 2 (NLP), and Team 3 (analytics engine) into a user-friendly UI.

---

### 🏗 Project Structure

```
Team4_module/
├── app.py                 # Main Streamlit app
├── auth.py                # Authentication (Google OAuth login)
├── users.json             # User data storage
├── scripts/
│   └── run_visualization.py
├── visualization/
│   ├── dashboard.py       # Main dashboard layout
│   ├── charts.py          # Chart generation logic
│   ├── insights.py        # Insight display
│   ├── config.py          # Visualization settings
│   ├── nlp_bridge.py      # Connects NLP → Analytics → UI
│   └── __init__.py
├── reports/               # Generated charts/images
```

---

### 🚀 Features

* Secure login using Google OAuth
* Interactive dashboard UI (Streamlit)
* KPI cards and visual charts
* Integration with NLP and Analytics modules
* Real-time insights display
* Modular and scalable design

---

### 🔗 Integration Flow

User Query → NLP Module → Structured Query → Analytics Engine → Visualization Dashboard

---

### ▶️ How to Run

1️⃣ Install dependencies

```
pip install -r requirements.txt
```

2️⃣ Run Streamlit app

```
streamlit run Team4_module/app.py
```

---

### ⚠️ Environment Setup

Create a `.env` file in the project root:

```
CLIENT_ID=your_google_client_id
CLIENT_SECRET=your_google_client_secret
```

⚠️ Do NOT commit `.env` to GitHub.

---

### ✅ Output

* Interactive dashboard with charts and KPIs
* Visual insights based on user queries
* Seamless integration across all modules
