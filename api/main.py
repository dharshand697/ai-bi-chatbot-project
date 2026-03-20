from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd

# ✅ Initialize app FIRST
app = FastAPI()

# ✅ Request schema
class QueryRequest(BaseModel):
    query: str

# ✅ Imports (after app is fine too, but keep clean)
from analytics_engine.core.engine import process_query
from analytics_engine.core.query_validator import validate_query
from analytics_engine.utils.data_loader import load_dataset
from analytics_engine.processors.filter_processor import apply_filters
from analytics_engine.forecasting.forecast_engine import forecast_metric


# ✅ Root endpoint
@app.get("/")
def home():
    return {"message": "AI BI Chatbot API is running 🚀"}


# ✅ Main endpoint
@app.post("/analyze")
def analyze(request: QueryRequest):
    return process_query(request.query)


# ---- TESTING ENDPOINTS ----

# 1️⃣ NLP Test
@app.post("/test/validate")
def test_validate(request: QueryRequest):
    try:
        result = validate_query(request.query)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# 2️⃣ Data Loader Test
@app.get("/test/data")
def test_data():
    df = load_dataset()
    return {
        "rows": len(df),
        "columns": list(df.columns)
    }


# 3️⃣ Filter Test
@app.post("/test/filter")
def test_filter(request: QueryRequest):
    return process_query(request.query)
    

# 4️⃣ Engine Test
@app.post("/test/engine")
def test_engine(request: QueryRequest):
    return process_query(request.query)


# 5️⃣ Forecast Test
@app.get("/test/forecast")
def test_forecast():
    try:
        df = load_dataset()

        # ✅ Check columns
        if "orderdate" not in df.columns:
            return {"status": "error", "message": "orderdate column missing"}

        if "sales" not in df.columns:
            return {"status": "error", "message": "sales column missing"}

        # ✅ Convert date
        df["orderdate"] = pd.to_datetime(df["orderdate"], errors="coerce")

        # ✅ Drop invalid rows
        df = df.dropna(subset=["orderdate", "sales"])

        # ✅ Sort (important for forecasting)
        df = df.sort_values("orderdate")

        # ✅ Aggregate
        df_grouped = df.groupby("orderdate")["sales"].sum().reset_index()

        # ✅ Rename columns (VERY IMPORTANT)
        df_grouped.columns = ["date", "sales"]

        # ✅ Debug print (optional)
        print(df_grouped.head())

        # ✅ Forecast
        return forecast_metric(df_grouped, metric="sales")

    except Exception as e:
        return {"status": "error", "message": str(e)}