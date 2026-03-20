from analytics_engine.utils.data_loader import load_dataset
from analytics_engine.utils.metric_mapper import map_metric
from analytics_engine.utils.response_formatter import success_response, error_response
from analytics_engine.utils.query_parser import parse_query

from analytics_engine.core.query_validator import validate_query

from analytics_engine.processors.filter_processor import apply_filters
from analytics_engine.processors.groupby_processor import apply_groupby
from analytics_engine.processors.ranking_processor import apply_ranking

from analytics_engine.forecasting.forecast_engine import forecast_metric
from analytics_engine.insights.insight_generator import generate_insight


def process_query(query):
    try:
        df = load_dataset()

        # 🔥 CRITICAL FIX (ONLY THIS LOGIC)
        if isinstance(query, dict):
            query_text = query.get("query", "")
            query = parse_query(query_text)

        elif isinstance(query, str):
            query = parse_query(query)

        else:
            raise ValueError("Invalid query format")

        print("Parsed Query:", query)

        validate_query(query)

        metric = map_metric(query["metric"])

        df = apply_filters(df, query.get("filters"))

        if query.get("group_by"):
            df = apply_groupby(
                df,
                query["group_by"],
                metric,
                query.get("aggregation", "sum")
            )

        if query.get("top_n"):
            df = apply_ranking(df, metric, query["top_n"])

        if query.get("forecast"):
            forecast = forecast_metric(df, metric)
            return success_response(forecast)

        insight = generate_insight(df, metric)

        return success_response(
            df.to_dict(orient="records"),
            insight
        )

    except Exception as e:
        return error_response(str(e))