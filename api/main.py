"""
InsightAI — FastAPI Backend  (v3 — fully rewritten chat engine)
Connects InsightAI.html frontend → NLP pipeline (Team2) → Analytics engine (Team1)
"""

import os, sys, re, pickle
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Path setup ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "Team2_module"))
sys.path.insert(0, os.path.join(BASE_DIR, "analytics_engine"))
sys.path.insert(0, os.path.join(BASE_DIR, "analytics_engine", "core"))

from entity_extractor   import extract_entities
from query_builder      import build_query
from response_generator import generate_response
from analytics_engine.core.engine import process_query

# ── Load intent model ────────────────────────────────────────────────────────
MODELS_DIR = os.path.join(BASE_DIR, "models")
with open(os.path.join(MODELS_DIR, "intent_model.pkl"), "rb") as f:
    intent_model = pickle.load(f)
with open(os.path.join(MODELS_DIR, "vectorizer.pkl"), "rb") as f:
    vectorizer = pickle.load(f)

def classify_intent(text: str) -> dict:
    vec    = vectorizer.transform([text])
    intent = intent_model.predict(vec)[0]
    probs  = intent_model.predict_proba(vec)[0]
    return {"intent": intent, "confidence": round(float(probs.max()), 3)}

# ── Load CSV and build value-lookup maps ─────────────────────────────────────
CSV_PATH = os.path.join(BASE_DIR, "Team1_module", "data", "processed", "master_dataset.csv")
df_global = pd.read_csv(CSV_PATH)
df_global.columns = df_global.columns.str.lower().str.strip()
print(f"✅ Loaded dataset: {len(df_global)} rows | Columns: {list(df_global.columns)}")

# lowercase key → actual CSV value  (built from real data, not hardcoded)
PRODUCT_MAP   = {v.lower(): v for v in df_global["productline"].unique()} if "productline"  in df_global.columns else {}
COUNTRY_MAP   = {v.lower(): v for v in df_global["country"].unique()}     if "country"      in df_global.columns else {}
TERRITORY_MAP = {v.lower(): v for v in df_global["territory"].unique()}   if "territory"    in df_global.columns else {}
DEALSIZE_MAP  = {v.lower(): v for v in df_global["dealsize"].unique()}    if "dealsize"     in df_global.columns else {}

print(f"   Products:    {list(PRODUCT_MAP.values())}")
print(f"   Territories: {list(TERRITORY_MAP.values())}")
print(f"   Deal sizes:  {list(DEALSIZE_MAP.values())}")
print(f"   Countries:   {len(COUNTRY_MAP)} countries loaded")

# ── FastAPI ──────────────────────────────────────────────────────────────────
app = FastAPI(title="InsightAI API", version="3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    message: str


# ════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════════════

def fmt(v: float) -> str:
    if   v >= 1_000_000: return f"${v/1_000_000:.2f}M"
    elif v >= 1_000:     return f"${v/1_000:.1f}K"
    else:                return f"${v:,.2f}"


def extract_filters(msg: str) -> dict:
    """
    Match actual CSV values against the user message (longest match first).
    Returns {column: matched_value} — no guessing, only real data values.
    """
    m       = msg.lower()
    filters = {}

    # Products — e.g. "Classic Cars", "Vintage Cars", "Motorcycles"
    for key, val in sorted(PRODUCT_MAP.items(), key=lambda x: -len(x[0])):
        if key in m:
            filters["productline"] = val
            break

    # Territories — e.g. "EMEA", "NA", "Japan"
    for key, val in sorted(TERRITORY_MAP.items(), key=lambda x: -len(x[0])):
        if key in m:
            filters["territory"] = val
            break

    # Common territory aliases (user may say "North America" instead of "NA")
    if "territory" not in filters:
        TERR_ALIASES = {
            "north america": "NA", "north american": "NA",
            "emea": "EMEA", "europe": "EMEA", "middle east": "EMEA", "africa": "EMEA",
            "asia": "Japan", "apac": "Japan", "pacific": "Japan",
        }
        for alias, tval in TERR_ALIASES.items():
            if alias in m and tval in TERRITORY_MAP.values():
                filters["territory"] = tval
                break

    # Countries (only if no territory already matched)
    if "territory" not in filters:
        for key, val in sorted(COUNTRY_MAP.items(), key=lambda x: -len(x[0])):
            if key in m:
                filters["country"] = val
                break

    # Deal size — "small", "medium", "large"
    for key, val in sorted(DEALSIZE_MAP.items(), key=lambda x: -len(x[0])):
        if key in m:
            filters["dealsize"] = val
            break

    # Year filter — detect 4-digit years like 2003, 2004, 2005
    year_match = re.search(r'\b(200[3-9]|201\d|202\d)\b', m)
    if year_match:
        filters["year_id"] = int(year_match.group(1))

    # Quarter filter — detect "Q1", "Q2", "quarter 1", "first quarter" etc.
    qtr_map = {
        "q1": 1, "q2": 2, "q3": 3, "q4": 4,
        "quarter 1": 1, "quarter 2": 2, "quarter 3": 3, "quarter 4": 4,
        "first quarter": 1, "second quarter": 2, "third quarter": 3, "fourth quarter": 4,
    }
    for key, val in sorted(qtr_map.items(), key=lambda x: -len(x[0])):
        if key in m:
            filters["qtr_id"] = val
            break

    return filters


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    for col, val in filters.items():
        if col in df.columns:
            if df[col].dtype == object:
                df = df[df[col].str.lower() == str(val).lower()]
            else:
                df = df[df[col] == val]
    return df


def resolve_intent(msg: str, ml_intent: str, filters: dict) -> str:
    m = msg.lower()

    if any(w in m for w in ["hello", "hi ", "hey ", "good morning", "good afternoon",
                              "who are you", "what are you", "what can you", "help me", "help"]):
        return "greeting"

    # Orders count
    if any(w in m for w in ["how many order", "total order", "number of order",
                              "order count", "orders placed", "how many purchase"]):
        return "orders_query"

    # Average order value
    if any(w in m for w in ["average order", "avg order", "mean order",
                              "average sale", "avg sale", "average value",
                              "order value", "average revenue per order"]):
        return "avg_order_query"

    # Product count / catalog
    if any(w in m for w in ["how many product", "number of product", "product count",
                              "how many category", "categories do we", "product lines",
                              "how many line", "types of product"]):
        return "product_count_query"

    # Quarter analysis
    if any(w in m for w in ["quarter", "q1", "q2", "q3", "q4",
                              "best quarter", "which quarter", "quarterly best"]):
        return "quarter_query"

    # Customer queries
    if any(w in m for w in ["how many customer", "customer count", "number of customer",
                              "total customer", "unique customer", "how many client"]):
        return "customer_query"

    if any(w in m for w in ["trend", "over time", "monthly", "month by month",
                              "quarterly", "each month", "sales trend", "revenue trend",
                              "performance over", "growth over", "month wise", "monthwise"]):
        return "trend_query"

    if any(w in m for w in ["forecast", "predict", "next year", "future", "projection",
                              "expected revenue", "estimate", "next period"]):
        return "forecast_query"

    if any(w in m for w in ["compare", "comparison", "vs ", "versus", "year over year",
                              "yoy", "by year", "per year", "each year", "year wise",
                              "yearwise", "annual", "how did", "between year"]):
        return "comparison_query"

    if any(w in m for w in ["deal size", "deal sizes", "compare deal",
                              "small deal", "medium deal", "large deal"]):
        return "deal_query"

    if any(w in m for w in ["customer", "client", "buyer", "who bought",
                              "top customer", "best customer"]):
        return "customer_query"

    if any(w in m for w in ["top ", "best ", "highest ", "most ", "ranking",
                              "rank ", "leading ", "lowest ", "worst ", "bottom ",
                              "which product", "which country", "which region",
                              "which customer", "performance", "list"]):
        return "ranking_query"

    # Specific filter found + revenue/sales word → filtered sales query
    if filters and any(w in m for w in ["revenue", "sales", "how much", "total",
                                          "made", "earned", "generated", "what is",
                                          "show", "give me", "tell me"]):
        return "sales_query"

    if any(w in m for w in ["revenue", "sales", "how much", "total revenue",
                              "total sales", "overall", "what is the revenue",
                              "what are the sales", "show revenue"]):
        return "sales_query"

    return ml_intent


def extract_top_n(msg: str, default: int = 5) -> int:
    match = re.search(r'\b(\d+)\b', msg.lower())
    if match:
        n = int(match.group(1))
        if 1 <= n <= 50:
            return n
    return default


# ════════════════════════════════════════════════════════════════════════════
#  RESPONSE BUILDERS
# ════════════════════════════════════════════════════════════════════════════

def build_sales_response(df: pd.DataFrame, df_all: pd.DataFrame, filters: dict) -> str:
    if "sales" not in df.columns or df.empty:
        return "⚠️ No matching data found. Please check your filter — e.g. try *'Revenue for Classic Cars'* or *'Sales in EMEA'*."

    total     = float(df["sales"].sum())
    orders    = int(df["ordernumber"].nunique()) if "ordernumber" in df.columns else len(df)
    avg_order = total / orders if orders > 0 else 0

    parts = []
    if "productline" in filters: parts.append(f"**{filters['productline']}**")
    if "territory"   in filters: parts.append(f"**{filters['territory']}** region")
    if "country"     in filters: parts.append(f"**{filters['country']}**")
    if "dealsize"    in filters: parts.append(f"**{filters['dealsize']}** deals")
    label = " / ".join(parts) if parts else "All Data"

    lines = [f"📊 **Revenue for {label}: {fmt(total)}**\n"]
    lines.append(f"• Total Orders: **{orders:,}**")
    lines.append(f"• Avg Order Value: **{fmt(avg_order)}**")

    grand = float(df_all["sales"].sum())
    if grand > 0 and filters:
        pct = total / grand * 100
        lines.append(f"• Share of Overall Revenue: **{pct:.1f}%**")

    if "productline" not in filters and "productline" in df.columns and df["productline"].nunique() > 1:
        lines.append(f"• Top Product Line: **{df.groupby('productline')['sales'].sum().idxmax()}**")
    if "country" not in filters and "country" in df.columns:
        lines.append(f"• Top Country: **{df.groupby('country')['sales'].sum().idxmax()}**")
    if "territory" not in filters and "territory" in df.columns and df["territory"].nunique() > 1:
        lines.append(f"• Top Region: **{df.groupby('territory')['sales'].sum().idxmax()}**")

    return "\n".join(lines)


def build_ranking_response(df: pd.DataFrame, df_all: pd.DataFrame, msg: str, filters: dict) -> str:
    m = msg.lower()

    if   any(w in m for w in ["country","countries","nation","where"]):     grp = "country"
    elif any(w in m for w in ["region","territory","emea","apac","north america"]): grp = "territory"
    elif any(w in m for w in ["customer","client","buyer"]):                grp = "customername"
    elif any(w in m for w in ["deal size","deal"]):                         grp = "dealsize"
    elif any(w in m for w in ["product","category","productline",
                               "classic","vintage","motorcycle",
                               "truck","plane","ship","train"]):             grp = "productline"
    else:                                                                   grp = "productline"

    if grp not in df.columns or df.empty:
        grp = "productline"

    is_bottom = any(w in m for w in ["lowest","worst","bottom","least","minimum"])
    top_n     = extract_top_n(msg)
    grand_tot = float(df_all["sales"].sum())

    grouped = (
        df.groupby(grp)["sales"].sum()
        .sort_values(ascending=is_bottom)
        .head(top_n)
        .reset_index()
    )

    rank_word  = "Bottom" if is_bottom else "Top"
    col_label  = grp.replace("_"," ").title()
    filter_ctx = ""
    if "territory" in filters: filter_ctx = f" in **{filters['territory']}**"
    if "country"   in filters: filter_ctx = f" in **{filters['country']}**"

    lines  = [f"🏆 **{rank_word} {top_n} by {col_label}{filter_ctx}:**\n"]
    medals = ["🥇","🥈","🥉"]

    for i, row in grouped.iterrows():
        val   = row["sales"]
        name  = row[grp]
        pct   = val / grand_tot * 100 if grand_tot > 0 else 0
        badge = medals[i] if i < 3 and not is_bottom else f"**{i+1}.**"
        lines.append(f"{badge} {name}  —  {fmt(val)}  ({pct:.1f}% of total)")

    return "\n".join(lines)


def build_comparison_response(df: pd.DataFrame, filters: dict) -> str:
    if "year_id" not in df.columns or df.empty:
        return "⚠️ Year data not available for comparison."

    grouped  = df.groupby("year_id")["sales"].sum().reset_index().sort_values("year_id")
    flabel   = f" — {filters.get('productline') or filters.get('territory','')}" if filters else ""
    lines    = [f"⚖️ **Year-over-Year Revenue Comparison{flabel}**\n"]
    prev_val = None

    for _, row in grouped.iterrows():
        yr, val = int(row["year_id"]), row["sales"]
        if prev_val is not None:
            chg   = (val - prev_val) / prev_val * 100
            arrow = "▲" if chg >= 0 else "▼"
            lines.append(f"• **{yr}**: {fmt(val)}  {arrow} {chg:+.1f}% vs {yr-1}")
        else:
            lines.append(f"• **{yr}**: {fmt(val)}  (baseline year)")
        prev_val = val

    total = float(df["sales"].sum())
    best  = grouped.loc[grouped["sales"].idxmax()]
    lines.append(f"\n📊 **3-Year Total: {fmt(total)}**")
    lines.append(f"🏆 **Best Year: {int(best['year_id'])}** with {fmt(best['sales'])}")
    return "\n".join(lines)


def build_forecast_response(df: pd.DataFrame, filters: dict) -> str:
    if "year_id" not in df.columns or df.empty:
        return "⚠️ Time series data not available for forecasting."

    yearly = df.groupby("year_id")["sales"].sum().sort_index()
    if len(yearly) < 2:
        return "⚠️ Not enough historical data to generate a forecast."

    growth   = (yearly.iloc[-1] - yearly.iloc[-2]) / yearly.iloc[-2]
    forecast = yearly.iloc[-1] * (1 + growth)
    last_yr  = int(yearly.index[-1])
    flabel   = f" — {filters.get('productline') or filters.get('territory','')}" if filters else ""

    lines = [f"🔮 **Revenue Forecast{flabel}**\n"]
    for yr, val in yearly.items():
        lines.append(f"• **{int(yr)}** (actual): {fmt(val)}")
    lines.append(f"\n• **{last_yr+1}** (projected): **{fmt(forecast)}**")
    lines.append(f"\n📈 Applied {growth*100:+.1f}% year-on-year growth rate.")
    lines.append(f"⚠️ Linear projection only — actual results may vary.")
    return "\n".join(lines)


def build_trend_response(df: pd.DataFrame, filters: dict) -> str:
    if "month_id" not in df.columns or "year_id" not in df.columns or df.empty:
        return "⚠️ Monthly trend data not available."

    MONTHS = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
              7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    flabel  = f" — {filters.get('productline') or filters.get('territory','')}" if filters else ""
    monthly = df.groupby(["year_id","month_id"])["sales"].sum().reset_index()
    lines   = [f"📈 **Monthly Sales Trend{flabel}**\n"]

    for yr in sorted(monthly["year_id"].unique()):
        yr_data  = monthly[monthly["year_id"]==yr].sort_values("month_id")
        yr_total = yr_data["sales"].sum()
        max_val  = yr_data["sales"].max()
        lines.append(f"**{int(yr)}**  (Total: {fmt(yr_total)})")
        for _, row in yr_data.iterrows():
            bar = "█" * (int(row["sales"]/max_val*12) if max_val > 0 else 0)
            mn  = MONTHS.get(int(row["month_id"]), str(int(row["month_id"])))
            lines.append(f"  {mn:3s}  {bar:<12}  {fmt(row['sales'])}")
        lines.append("")

    yearly = df.groupby("year_id")["sales"].sum().sort_index()
    if len(yearly) >= 2:
        chg = (yearly.iloc[-1] - yearly.iloc[-2]) / yearly.iloc[-2] * 100
        lines.append(f"{'📈' if chg>=0 else '📉'} Year-on-year change: **{chg:+.1f}%**")

    return "\n".join(lines)


def build_customer_response(df: pd.DataFrame) -> str:
    if "customername" not in df.columns or df.empty:
        return "⚠️ Customer data not available."

    total_cust = int(df["customername"].nunique())
    total_ord  = int(df["ordernumber"].nunique()) if "ordernumber" in df.columns else len(df)
    total_rev  = float(df["sales"].sum())
    avg_cust   = total_rev / total_cust if total_cust > 0 else 0
    top5       = df.groupby("customername")["sales"].sum().sort_values(ascending=False).head(5)
    medals     = ["🥇","🥈","🥉"]

    lines = [
        f"👥 **Customer Overview**\n",
        f"• Total Unique Customers: **{total_cust:,}**",
        f"• Total Orders: **{total_ord:,}**",
        f"• Total Revenue: **{fmt(total_rev)}**",
        f"• Avg Revenue per Customer: **{fmt(avg_cust)}**\n",
        f"🏆 **Top 5 Customers by Revenue:**",
    ]
    for i, (name, val) in enumerate(top5.items()):
        lines.append(f"{medals[i] if i<3 else str(i+1)+'.'} {name} — {fmt(val)}")
    return "\n".join(lines)


def build_orders_response(df: pd.DataFrame, filters: dict) -> str:
    if df.empty:
        return "⚠️ No matching data found for your filter."
    orders     = int(df["ordernumber"].nunique()) if "ordernumber" in df.columns else len(df)
    total_rev  = float(df["sales"].sum())
    avg_order  = total_rev / orders if orders > 0 else 0
    lines      = [f"📦 **Order Summary**\n"]
    if filters:
        parts = []
        if "productline" in filters: parts.append(f"**{filters['productline']}**")
        if "territory"   in filters: parts.append(f"**{filters['territory']}** region")
        if "country"     in filters: parts.append(f"**{filters['country']}**")
        if "year_id"     in filters: parts.append(f"**{filters['year_id']}**")
        lines[0] = f"📦 **Order Summary for {' / '.join(parts)}**\n"
    lines.append(f"• Total Orders Placed: **{orders:,}**")
    lines.append(f"• Total Revenue from Orders: **{fmt(total_rev)}**")
    lines.append(f"• Avg Revenue per Order: **{fmt(avg_order)}**")
    if "year_id" in df.columns and "year_id" not in filters:
        by_year = df.groupby("year_id")["ordernumber"].nunique()
        lines.append(f"\n📅 **Orders by Year:**")
        for yr, cnt in by_year.items():
            lines.append(f"  • {int(yr)}: **{cnt:,}** orders")
    return "\n".join(lines)


def build_avg_order_response(df: pd.DataFrame, filters: dict) -> str:
    if df.empty:
        return "⚠️ No matching data found."
    orders    = int(df["ordernumber"].nunique()) if "ordernumber" in df.columns else len(df)
    total_rev = float(df["sales"].sum())
    avg_order = total_rev / orders if orders > 0 else 0
    lines = [f"💰 **Average Order Value**\n"]
    lines.append(f"• Avg Order Value (AOV): **{fmt(avg_order)}**")
    lines.append(f"• Based on {orders:,} orders totalling **{fmt(total_rev)}**")
    if "dealsize" in df.columns:
        lines.append(f"\n💼 **AOV by Deal Size:**")
        for ds, grp in df.groupby("dealsize"):
            cnt = grp["ordernumber"].nunique() if "ordernumber" in grp.columns else len(grp)
            rev = float(grp["sales"].sum())
            lines.append(f"  • {ds}: **{fmt(rev/cnt if cnt else 0)}**  ({cnt:,} orders)")
    return "\n".join(lines)


def build_quarter_response(df: pd.DataFrame, filters: dict) -> str:
    if "qtr_id" not in df.columns or df.empty:
        return "⚠️ Quarterly data not available."
    qtrs   = df.groupby("qtr_id")["sales"].sum().reset_index().sort_values("qtr_id")
    total  = qtrs["sales"].sum()
    best   = qtrs.loc[qtrs["sales"].idxmax()]
    worst  = qtrs.loc[qtrs["sales"].idxmin()]
    lines  = ["📅 **Quarterly Revenue Breakdown**\n"]
    for _, row in qtrs.iterrows():
        q   = int(row["qtr_id"])
        val = row["sales"]
        pct = val / total * 100 if total > 0 else 0
        bar = "█" * int(pct / 5)
        lines.append(f"• **Q{q}**: {fmt(val)}  ({pct:.1f}%)  {bar}")
    lines.append(f"\n🏆 **Best Quarter: Q{int(best['qtr_id'])}** with {fmt(best['sales'])}")
    lines.append(f"📉 **Weakest Quarter: Q{int(worst['qtr_id'])}** with {fmt(worst['sales'])}")
    # Breakdown by year if available
    if "year_id" in df.columns and "year_id" not in filters:
        lines.append(f"\n📊 **Best Quarter per Year:**")
        for yr, grp in df.groupby("year_id"):
            best_q = grp.groupby("qtr_id")["sales"].sum().idxmax()
            best_v = grp.groupby("qtr_id")["sales"].sum().max()
            lines.append(f"  • **{int(yr)}** → Q{int(best_q)}: {fmt(best_v)}")
    return "\n".join(lines)


def build_product_count_response(df: pd.DataFrame) -> str:
    lines = ["🗂️ **Product Catalog Overview**\n"]
    if "productline" in df.columns:
        product_lines = df["productline"].nunique()
        lines.append(f"• Total Product Lines: **{product_lines}**")
        lines.append(f"\n📦 **Revenue by Product Line:**")
        by_prod = df.groupby("productline")["sales"].sum().sort_values(ascending=False)
        grand   = by_prod.sum()
        medals  = ["🥇","🥈","🥉"]
        for i, (name, val) in enumerate(by_prod.items()):
            pct   = val / grand * 100 if grand > 0 else 0
            badge = medals[i] if i < 3 else f"{i+1}."
            lines.append(f"  {badge} {name}: {fmt(val)}  ({pct:.1f}%)")
    if "productcode" in df.columns:
        lines.append(f"\n• Total Unique Product Codes: **{df['productcode'].nunique():,}**")
    return "\n".join(lines)



    if "dealsize" not in df.columns or df.empty:
        return "⚠️ Deal size data not available."

    deal  = df.groupby("dealsize").agg(
        revenue=("sales","sum"), orders=("ordernumber","nunique")
    ).reset_index().sort_values("revenue", ascending=False)
    total = deal["revenue"].sum()

    lines = ["💼 **Revenue by Deal Size**\n"]
    for _, row in deal.iterrows():
        pct = row["revenue"]/total*100 if total>0 else 0
        aov = row["revenue"]/row["orders"] if row["orders"]>0 else 0
        lines.append(
            f"• **{row['dealsize']}**: {fmt(row['revenue'])}  "
            f"({pct:.1f}%) — {int(row['orders']):,} orders  |  AOV: {fmt(aov)}"
        )
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
#  API ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    return {"status":"ok","dataset_rows":len(df_global),"columns":list(df_global.columns)}


@app.get("/api/dashboard")
def dashboard():
    df = df_global.copy()
    total_revenue = float(df["sales"].sum())
    total_orders  = int(df["ordernumber"].nunique()) if "ordernumber" in df.columns else len(df)
    countries     = int(df["country"].nunique())     if "country"     in df.columns else 0
    customers     = int(df["customername"].nunique()) if "customername" in df.columns else 0

    def agg(col, label_fn=None):
        if col not in df.columns: return [],[]
        raw = df.groupby(col)["sales"].sum().reset_index().sort_values(col)
        lbls = [label_fn(v) if label_fn else str(v) for v in raw[col]]
        return lbls, raw["sales"].round(2).tolist()

    ml, mv = agg("month_id")
    ql, qv = agg("qtr_id",  lambda q: f"Q{q}")
    yl, yv = agg("year_id")

    return {
        "kpi":{"total_revenue":round(total_revenue,2),"total_orders":total_orders,
               "countries":countries,"customers":customers},
        "monthly":{"labels":ml,"values":mv},
        "quarterly":{"labels":ql,"values":qv},
        "yearly":{"labels":yl,"values":yv},
    }


@app.get("/api/charts/{chart_type}")
def charts(chart_type: str):
    df  = df_global.copy()
    col = {"country":"country","product":"productline","dealsize":"dealsize",
           "customers":"customername","territory":"territory"}.get(chart_type)
    if not col or col not in df.columns:
        raise HTTPException(400, f"Unknown chart type: {chart_type}")
    top  = 10 if chart_type in ("country","customers") else None
    data = df.groupby(col)["sales"].sum().sort_values(ascending=False)
    if top: data = data.head(top)
    return {"labels":data.index.tolist(),"values":data.round(2).tolist()}


@app.get("/api/analytics")
def analytics():
    df = df_global.copy()
    yearly = df.groupby("year_id")["sales"].sum().round(2).to_dict() if "year_id" in df.columns else {}
    dr     = f"{int(df['year_id'].min())} – {int(df['year_id'].max())}" if "year_id" in df.columns else "N/A"
    return {
        "total_records": len(df), "null_count": int(df.isnull().sum().sum()),
        "date_range": dr, "yearly_volume": {str(k):v for k,v in yearly.items()},
        "columns": list(df.columns),
        "product_lines": int(df["productline"].nunique()) if "productline" in df.columns else 0,
        "countries": int(df["country"].nunique()) if "country" in df.columns else 0,
    }


@app.post("/api/chat")
def chat(req: ChatRequest):
    user_message = req.message.strip()
    if not user_message:
        raise HTTPException(400, "Empty message")

    try:
        msg = user_message.lower()

        # Step 1 — ML intent (baseline)
        intent_result = classify_intent(user_message)
        ml_intent     = intent_result["intent"]
        confidence    = intent_result["confidence"]

        # Step 2 — Extract filters directly from CSV values (most reliable)
        filters = extract_filters(msg)

        # Step 3 — Keyword-based intent override
        intent = resolve_intent(user_message, ml_intent, filters)

        # Step 4 — Team2 NLP pipeline (for structured_query metadata)
        entities             = extract_entities(user_message)
        entities["raw_text"] = msg
        structured_query     = build_query(intent, entities)

        # Step 5 — Apply filters
        df_filtered = apply_filters(df_global.copy(), filters)

        # Step 6 — Route to response builder
        if   intent == "greeting":           final_response = (
            "👋 **Hello! I'm InsightAI**, your intelligent data analyst.\n\n"
            "I have access to **2,823 sales records** spanning 19 countries from 2003–2005. "
            "Here's what I can help with:\n\n"
            "• 📊 **Revenue & Sales** — total, filtered by product, region, country, deal size, year\n"
            "• 🏆 **Rankings** — top/bottom N by any dimension\n"
            "• 📈 **Trends** — monthly & yearly patterns with visual bars\n"
            "• 🔮 **Forecasts** — next-year revenue projection\n"
            "• ⚖️ **Year Comparison** — year-over-year with % change\n"
            "• 📅 **Quarterly** — best quarter, Q1/Q2/Q3/Q4 breakdown\n"
            "• 💼 **Deal Sizes** — Small / Medium / Large analysis\n"
            "• 👥 **Customers** — count, top buyers, average spend\n"
            "• 📦 **Orders** — total orders, average order value\n"
            "• 🗂️ **Products** — catalog overview, all product lines\n\n"
            "**Example questions:**\n"
            "• *Revenue for Classic Cars*  •  *Sales in North America*\n"
            "• *Top 10 countries by revenue*  •  *Sales in 2004*\n"
            "• *Compare sales by year*  •  *Which quarter was best?*\n"
            "• *How many orders were placed?*  •  *Average order value*"
        )
        elif intent == "orders_query":        final_response = build_orders_response(df_filtered, filters)
        elif intent == "avg_order_query":     final_response = build_avg_order_response(df_filtered, filters)
        elif intent == "quarter_query":       final_response = build_quarter_response(df_filtered, filters)
        elif intent == "product_count_query": final_response = build_product_count_response(df_filtered)
        elif intent == "customer_query":      final_response = build_customer_response(df_filtered)
        elif intent == "trend_query":         final_response = build_trend_response(df_filtered, filters)
        elif intent == "forecast_query":      final_response = build_forecast_response(df_filtered, filters)
        elif intent == "comparison_query":    final_response = build_comparison_response(df_filtered, filters)
        elif intent == "deal_query":          final_response = build_deal_response(df_filtered, df_global)
        elif intent == "ranking_query":       final_response = build_ranking_response(df_filtered, df_global, user_message, filters)
        elif intent == "sales_query":         final_response = build_sales_response(df_filtered, df_global, filters)
        else:
            result         = process_query(structured_query)
            final_response = generate_response(result)

        return {
            "response":         final_response,
            "intent":           intent,
            "confidence":       confidence,
            "entities":         entities,
            "structured_query": structured_query,
            "filters_detected": filters,
        }

    except Exception as e:
        import traceback; traceback.print_exc()
        return {
            "response":   f"⚠️ Sorry, I couldn't process that. Error: {str(e)}",
            "intent":     "unknown", "confidence": 0.0,
            "entities":   {}, "structured_query": {}, "filters_detected": {},
        }


@app.get("/api/nlp/status")
def nlp_status():
    rp = os.path.join(BASE_DIR, "reports", "intent_accuracy.txt")
    return {
        "status": "ready",
        "model":  "TF-IDF + Logistic Regression + Keyword Override v3",
        "intents": ["sales_query","ranking_query","comparison_query","forecast_query",
                    "trend_query","customer_query","deal_query","greeting"],
        "known_products":    list(PRODUCT_MAP.values()),
        "known_territories": list(TERRITORY_MAP.values()),
        "accuracy_report":   open(rp).read() if os.path.exists(rp) else "",
    }