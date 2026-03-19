from fastapi import FastAPI
from pydantic import BaseModel

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
    df = load_dataset()
    filtered_df = apply_filters(df, request.query)
    
    return {
        "rows_after_filter": len(filtered_df)
    }


# 4️⃣ Engine Test
@app.post("/test/engine")
def test_engine(request: QueryRequest):
    return process_query(request.query)


# 5️⃣ Forecast Test
@app.get("/test/forecast")
def test_forecast():
    df = load_dataset()
    return forecast_metric(df, metric="sales")