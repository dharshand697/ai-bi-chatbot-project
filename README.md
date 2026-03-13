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
    python nlp/intent_classifier.py
### how to run test file
    python nlp/test_interactive.py

### Output
- `models/intent_model.pkl` - trained classifier
- `models/vectorizer.pkl` - fitted TF-IDF vectorizer
- `reports/intent_accuracy.txt` - accuracy report

### Dependencies
- scikit-learn

--