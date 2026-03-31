"""
InsightAI — Backend API Routes
================================
Drop this file into your project root (same folder as main.py).
Then add this to your main.py:

    from api_routes import router
    app.include_router(router)

Endpoints exposed:
  GET  /api/dashboard          → KPIs + monthly/quarterly revenue
  GET  /api/charts/product     → Revenue by product line
  GET  /api/charts/country     → Top countries by revenue
  GET  /api/charts/dealsize    → Revenue by deal size
  GET  /api/charts/territory   → Revenue by territory/region
  POST /api/chat               → NLP chatbot query
  GET  /api/health             → Health check
"""

import os, re
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

router = APIRouter()

# ── Locate the CSV file ─────────────────────────────────────────
# Tries common locations — adjust DATA_PATH if your CSV is elsewhere
_SEARCH_PATHS = [
    "data/sales_data_sample.csv",
    "data/sales_data.csv",
    "sales_data_sample.csv",
    "sales_data.csv",
    "data/data.csv",
    "dataset.csv",
]

def _find_csv() -> Optional[Path]:
    for p in _SEARCH_PATHS:
        path = Path(p)
        if path.exists():
            return path
    # Last resort: search current dir recursively for first .csv
    for path in Path(".").rglob("*.csv"):
        return path
    return None

def _load_df() -> pd.DataFrame:
    csv_path = _find_csv()
    if csv_path is None:
        raise FileNotFoundError("No CSV data file found. Check _SEARCH_PATHS in api_routes.py")
    df = pd.read_csv(csv_path, encoding="latin-1")
    df.columns = [c.strip().upper() for c in df.columns]  # normalise column names
    # Make sure SALES column is numeric
    if "SALES" in df.columns:
        df["SALES"] = pd.to_numeric(df["SALES"], errors="coerce").fillna(0)
    return df


# ── Helper: map column names flexibly ──────────────────────────
def _col(df: pd.DataFrame, *candidates: str) -> Optional[str]:
    """Return the first candidate column that exists in df."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


# ═══════════════════════════════════════════════════════════════
#  GET /api/health
# ═══════════════════════════════════════════════════════════════
@router.get("/api/health")
def health():
    try:
        df = _load_df()
        return {"status": "ok", "rows": len(df)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ═══════════════════════════════════════════════════════════════
#  GET /api/dashboard   →  KPIs + monthly + quarterly revenue
# ═══════════════════════════════════════════════════════════════
@router.get("/api/dashboard")
def dashboard():
    df = _load_df()

    sales_col      = _col(df, "SALES", "REVENUE", "AMOUNT")
    order_col      = _col(df, "ORDERNUMBER", "ORDER_ID", "ORDER_NUMBER", "ID")
    customer_col   = _col(df, "CUSTOMERNAME", "CUSTOMER", "CUSTOMER_NAME")
    country_col    = _col(df, "COUNTRY")
    month_col      = _col(df, "MONTH_ID", "MONTH", "ORDERMONTH")
    quarter_col    = _col(df, "QTR_ID", "QUARTER", "QTR")
    year_col       = _col(df, "YEAR_ID", "YEAR", "ORDERYEAR")

    total_revenue  = round(df[sales_col].sum(), 2) if sales_col else 0
    total_orders   = df[order_col].nunique() if order_col else len(df)
    customers      = df[customer_col].nunique() if customer_col else 0
    countries      = df[country_col].nunique() if country_col else 0

    # Monthly revenue (across all years, grouped by month number)
    monthly = {"labels": [], "values": []}
    if sales_col and month_col:
        m = df.groupby(month_col)[sales_col].sum().sort_index()
        monthly["labels"] = [str(x) for x in m.index.tolist()]
        monthly["values"] = [round(v, 2) for v in m.values.tolist()]

    # Quarterly revenue
    quarterly = {"labels": [], "values": []}
    if sales_col and quarter_col:
        q = df.groupby(quarter_col)[sales_col].sum().sort_index()
        quarterly["labels"] = [f"Q{x}" for x in q.index.tolist()]
        quarterly["values"] = [round(v, 2) for v in q.values.tolist()]
    elif sales_col and month_col:
        # Derive quarters from months if no QTR column
        df["_QTR"] = ((df[month_col].astype(int) - 1) // 3 + 1)
        q = df.groupby("_QTR")[sales_col].sum().sort_index()
        quarterly["labels"] = [f"Q{x}" for x in q.index.tolist()]
        quarterly["values"] = [round(v, 2) for v in q.values.tolist()]

    return {
        "kpi": {
            "total_revenue": total_revenue,
            "total_orders":  total_orders,
            "customers":     customers,
            "countries":     countries,
        },
        "monthly":   monthly,
        "quarterly": quarterly,
    }


# ═══════════════════════════════════════════════════════════════
#  GET /api/charts/product   → Revenue by product line
# ═══════════════════════════════════════════════════════════════
@router.get("/api/charts/product")
def charts_product():
    df = _load_df()
    sales_col   = _col(df, "SALES", "REVENUE", "AMOUNT")
    product_col = _col(df, "PRODUCTLINE", "PRODUCT_LINE", "PRODUCT", "CATEGORY")

    if not sales_col or not product_col:
        return {"labels": [], "values": []}

    grp = (
        df.groupby(product_col)[sales_col]
        .sum()
        .sort_values(ascending=False)
    )
    return {
        "labels": grp.index.tolist(),
        "values": [round(v, 2) for v in grp.values.tolist()],
    }


# ═══════════════════════════════════════════════════════════════
#  GET /api/charts/country   → Top 10 countries by revenue
# ═══════════════════════════════════════════════════════════════
@router.get("/api/charts/country")
def charts_country():
    df = _load_df()
    sales_col   = _col(df, "SALES", "REVENUE", "AMOUNT")
    country_col = _col(df, "COUNTRY")

    if not sales_col or not country_col:
        return {"labels": [], "values": []}

    grp = (
        df.groupby(country_col)[sales_col]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    return {
        "labels": grp.index.tolist(),
        "values": [round(v, 2) for v in grp.values.tolist()],
    }


# ═══════════════════════════════════════════════════════════════
#  GET /api/charts/dealsize  → Revenue by deal size
# ═══════════════════════════════════════════════════════════════
@router.get("/api/charts/dealsize")
def charts_dealsize():
    df = _load_df()
    sales_col = _col(df, "SALES", "REVENUE", "AMOUNT")
    deal_col  = _col(df, "DEALSIZE", "DEAL_SIZE", "DEAL")

    if not sales_col or not deal_col:
        return {"labels": [], "values": []}

    grp = (
        df.groupby(deal_col)[sales_col]
        .sum()
        .sort_values(ascending=False)
    )
    return {
        "labels": grp.index.tolist(),
        "values": [round(v, 2) for v in grp.values.tolist()],
    }


# ═══════════════════════════════════════════════════════════════
#  GET /api/charts/territory → Revenue by territory/region
# ═══════════════════════════════════════════════════════════════
@router.get("/api/charts/territory")
def charts_territory():
    df = _load_df()
    sales_col     = _col(df, "SALES", "REVENUE", "AMOUNT")
    territory_col = _col(df, "TERRITORY", "REGION", "AREA")

    if not sales_col or not territory_col:
        return {"labels": [], "values": []}

    grp = (
        df.groupby(territory_col)[sales_col]
        .sum()
        .sort_values(ascending=False)
    )
    return {
        "labels": grp.index.tolist(),
        "values": [round(v, 2) for v in grp.values.tolist()],
    }


# ═══════════════════════════════════════════════════════════════
#  POST /api/chat   → NLP chatbot
# ═══════════════════════════════════════════════════════════════
class ChatRequest(BaseModel):
    message: str

@router.post("/api/chat")
def chat(req: ChatRequest):
    """
    Routes the user's message to the NLP module if available,
    otherwise falls back to a rule-based engine built from live CSV data.
    """
    query = req.message.strip()

    # ── Try to use your NLP module ──────────────────────────────
    # If your NLP module has a function like `get_answer(query)` or
    # `nlp_engine.query(text)`, import and call it here.
    # Example (uncomment and adjust import path):
    #
    # try:
    #     from nlp.engine import get_answer      # ← adjust to your module path
    #     result = get_answer(query)
    #     return {"response": result, "intent": "nlp_module", "confidence": 1.0}
    # except ImportError:
    #     pass  # NLP module not available — fall through to rule-based
    # except Exception as e:
    #     pass  # NLP error — fall through to rule-based

    # ── Rule-based fallback using live CSV data ─────────────────
    try:
        df    = _load_df()
        reply = _rule_based_answer(query, df)
    except Exception as e:
        reply = f"⚠️ Data error: {e}"

    return {
        "response":   reply,
        "intent":     _detect_intent(query),
        "confidence": 0.82,
    }


def _detect_intent(q: str) -> str:
    q = q.lower()
    if any(w in q for w in ["revenue", "sales", "total", "money", "earn"]):
        return "revenue_query"
    if any(w in q for w in ["product", "productline", "category", "item"]):
        return "product_query"
    if any(w in q for w in ["country", "countries", "region", "territory", "where"]):
        return "geo_query"
    if any(w in q for w in ["customer", "client", "buyer"]):
        return "customer_query"
    if any(w in q for w in ["deal", "size", "small", "medium", "large"]):
        return "dealsize_query"
    if any(w in q for w in ["order", "orders", "transaction"]):
        return "order_query"
    if any(w in q for w in ["year", "month", "quarter", "trend", "time"]):
        return "time_query"
    if any(w in q for w in ["top", "best", "highest", "most"]):
        return "ranking_query"
    return "unknown"


def _fmt(value: float) -> str:
    """Format a number as $X.XXM or $XXXk"""
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:.0f}"


def _rule_based_answer(query: str, df: pd.DataFrame) -> str:
    q           = query.lower()
    sales_col   = _col(df, "SALES", "REVENUE", "AMOUNT")
    product_col = _col(df, "PRODUCTLINE", "PRODUCT_LINE", "PRODUCT", "CATEGORY")
    country_col = _col(df, "COUNTRY")
    customer_col= _col(df, "CUSTOMERNAME", "CUSTOMER", "CUSTOMER_NAME")
    order_col   = _col(df, "ORDERNUMBER", "ORDER_ID", "ORDER_NUMBER")
    deal_col    = _col(df, "DEALSIZE", "DEAL_SIZE", "DEAL")
    territory_col=_col(df, "TERRITORY", "REGION", "AREA")
    year_col    = _col(df, "YEAR_ID", "YEAR", "ORDERYEAR")
    month_col   = _col(df, "MONTH_ID", "MONTH", "ORDERMONTH")

    # ── Total revenue ───────────────────────────────────────────
    if any(w in q for w in ["total revenue", "total sales", "overall revenue", "how much"]):
        if sales_col:
            total = df[sales_col].sum()
            return f"💰 <strong>Total Revenue: {_fmt(total)}</strong><br>Across {len(df):,} transactions."

    # ── Top products ────────────────────────────────────────────
    if any(w in q for w in ["product", "productline", "top product", "best product", "category"]):
        if sales_col and product_col:
            grp = df.groupby(product_col)[sales_col].sum().sort_values(ascending=False)
            n = 5
            lines = [f"• {lbl}: {_fmt(val)}" for lbl, val in list(grp.items())[:n]]
            return (f"🏆 <strong>Top: {grp.index[0]} — {_fmt(grp.iloc[0])}</strong><br>"
                    + "<br>".join(lines[1:]))

    # ── Top countries ────────────────────────────────────────────
    if any(w in q for w in ["country", "countries", "nation", "where"]):
        if sales_col and country_col:
            grp = df.groupby(country_col)[sales_col].sum().sort_values(ascending=False).head(5)
            lines = [f"• {lbl}: {_fmt(val)}" for lbl, val in grp.items()]
            return "🌍 <strong>Top Countries by Revenue:</strong><br>" + "<br>".join(lines)

    # ── Territory / Region ───────────────────────────────────────
    if any(w in q for w in ["region", "territory", "area"]):
        if sales_col and territory_col:
            grp = df.groupby(territory_col)[sales_col].sum().sort_values(ascending=False)
            lines = [f"• {lbl}: {_fmt(val)}" for lbl, val in grp.items()]
            return "🗺️ <strong>Revenue by Region:</strong><br>" + "<br>".join(lines)

    # ── Customers ────────────────────────────────────────────────
    if any(w in q for w in ["customer", "client", "buyer", "how many customer"]):
        if customer_col:
            count = df[customer_col].nunique()
            if sales_col:
                grp = df.groupby(customer_col)[sales_col].sum().sort_values(ascending=False).head(3)
                tops = ", ".join([f"{n} ({_fmt(v)})" for n, v in grp.items()])
                return (f"👥 <strong>{count} unique customers</strong><br>"
                        f"Top 3: {tops}")
            return f"👥 <strong>{count} unique customers</strong>"

    # ── Deal sizes ───────────────────────────────────────────────
    if any(w in q for w in ["deal", "deal size", "small", "medium", "large"]):
        if sales_col and deal_col:
            grp = df.groupby(deal_col)[sales_col].sum().sort_values(ascending=False)
            lines = [f"• {lbl}: {_fmt(val)}" for lbl, val in grp.items()]
            return "📦 <strong>Revenue by Deal Size:</strong><br>" + "<br>".join(lines)

    # ── Orders ───────────────────────────────────────────────────
    if any(w in q for w in ["order", "transaction", "how many order"]):
        count = df[order_col].nunique() if order_col else len(df)
        return f"📋 <strong>{count:,} total orders</strong> in the dataset."

    # ── Year / trend ─────────────────────────────────────────────
    if any(w in q for w in ["year", "annual", "yearly"]):
        if sales_col and year_col:
            grp = df.groupby(year_col)[sales_col].sum().sort_index()
            lines = [f"• {yr}: {_fmt(val)}" for yr, val in grp.items()]
            return "📅 <strong>Revenue by Year:</strong><br>" + "<br>".join(lines)

    # ── Month / trend ────────────────────────────────────────────
    if any(w in q for w in ["month", "monthly"]):
        if sales_col and month_col:
            grp = df.groupby(month_col)[sales_col].sum().sort_index()
            best_month = grp.idxmax()
            MONTHS = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                      7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
            best_name = MONTHS.get(int(best_month), str(best_month))
            return (f"📆 <strong>Best Month: {best_name} ({_fmt(grp.max())})</strong><br>"
                    f"Monthly average: {_fmt(grp.mean())}")

    # ── Top ranking ──────────────────────────────────────────────
    if any(w in q for w in ["top", "best", "highest", "most"]):
        if sales_col and product_col:
            best = df.groupby(product_col)[sales_col].sum().idxmax()
            val  = df.groupby(product_col)[sales_col].sum().max()
            return f"🥇 <strong>Top performer: {best}</strong> with {_fmt(val)} in revenue."

    # ── Default ──────────────────────────────────────────────────
    if sales_col:
        total = df[sales_col].sum()
        orders = df[order_col].nunique() if order_col else len(df)
        custs  = df[customer_col].nunique() if customer_col else "N/A"
        return (f"📊 <strong>Dataset Summary:</strong><br>"
                f"• Total Revenue: {_fmt(total)}<br>"
                f"• Orders: {orders:,}<br>"
                f"• Customers: {custs}<br><br>"
                f"Try asking: <em>total revenue, top products, top countries, revenue by year, deal sizes</em>")

    return "I couldn't find relevant data for your query. Try: 'total revenue', 'top products', 'top countries'."