from typing import Dict, Any


DEFAULT_AGGREGATIONS = {
    "sales_query":      "sum",
    "ranking_query":    "sum",
    "comparison_query": "sum",
    "forecast_query":   "sum"
}

# Default group_by per intent when none is specified
DEFAULT_GROUP_BY = {
    "ranking_query":    "productline",
    "comparison_query": "year_id",
}

# Keyword → column mapping for group_by detection
KEYWORD_GROUP_BY = {
    "country":     "country",
    "countries":   "country",
    "region":      "territory",
    "regions":     "territory",
    "territory":   "territory",
    "product":     "productline",
    "products":    "productline",
    "category":    "productline",
    "categories":  "productline",
    "customer":    "customername",
    "customers":   "customername",
    "year":        "year_id",
    "yearly":      "year_id",
    "quarter":     "qtr_id",
    "quarterly":   "qtr_id",
    "deal":        "dealsize",
    "deal size":   "dealsize",
    "city":        "city",
    "state":       "state",
}


def build_query(intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:

    group_by = entities.get("group_by")
    raw_text = entities.get("raw_text", "").lower()

    # Detect group_by from keywords in the raw query text
    if not group_by and raw_text:
        for keyword, column in KEYWORD_GROUP_BY.items():
            if keyword in raw_text:
                group_by = column
                break

    # If still no group_by, use sensible defaults per intent
    if not group_by and intent in DEFAULT_GROUP_BY:
        group_by = DEFAULT_GROUP_BY[intent]

    query = {
        "intent":      intent,
        "metric":      entities.get("metric", "sales"),
        "aggregation": DEFAULT_AGGREGATIONS.get(intent, "sum"),
        "group_by":    group_by,
        "filters":     entities.get("filters", {}),
    }

    # For sales_query with no group_by → return total only
    if intent == "sales_query" and not group_by:
        query["aggregate_total"] = True

    # Ranking logic
    if intent == "ranking_query":
        query["top_n"] = entities.get("top_n") or 5

    # Forecast logic
    if intent == "forecast_query":
        query["forecast"] = True

    return query