import re
from analytics_engine.config import METRIC_COLUMNS, SUPPORTED_AGGREGATIONS

def validate_query(query: str):
    query = query.lower()

    metric = None
    aggregation = None
    limit = None
    intent = "aggregation"  # default

    # 🔹 Detect metric
    for col in METRIC_COLUMNS:
        if col in query:
            metric = col
            break

    # 🔹 Detect aggregation
    for agg in SUPPORTED_AGGREGATIONS:
        if agg in query:
            aggregation = agg
            break

    # 🔹 Default aggregation
    if not aggregation:
        aggregation = "sum"

    # 🔹 Detect TOP N (ranking)
    if "top" in query:
        intent = "ranking"
        match = re.search(r'\d+', query)
        if match:
            limit = int(match.group())

    # 🔹 Validation
    if not metric:
        return {
            "status": "error",
            "message": "Metric Missing"
        }

    return {
        "status": "success",
        "intent": intent,
        "metric": metric,
        "aggregation": aggregation,
        "limit": limit
    }