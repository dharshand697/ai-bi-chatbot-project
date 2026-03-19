METRIC_MAP = {
    "revenue": "revenue",
    "sales": "revenue",
    "income": "revenue",
    "profit": "profit"
}

def map_metric(metric):
    return METRIC_MAP.get(metric.lower(),metric)