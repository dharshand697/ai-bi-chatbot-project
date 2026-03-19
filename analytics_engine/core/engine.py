from analytics_engine.utils.data_loader import load_dataset
from analytics_engine.utils.metric_mapper import map_metric
from analytics_engine.utils.response_formatter import success_response, error_response

from analytics_engine.core.query_validator import validate_query

from analytics_engine.processors.filter_processor import apply_filters
from analytics_engine.processors.groupby_processor import apply_groupby
from analytics_engine.processors.ranking_processor import apply_ranking

from analytics_engine.forecasting.forecast_engine import forecast_metric
from analytics_engine.insights.insight_generator import generate_insight

def process_query(query):
    try:
        df = load_dataset()

        #validate
        validate_query(query)

        #map metric
        metric = map_metric(query["metric"])

        #filter
        df = apply_filters(df, query.get("filters"))

        #groupby
        if query.get("group_by"):
            df = apply_groupby(
                df,
                query["group_by"],
                metric,
                query["aggregation"]
            )
        
        #ranking
        if query.get("top_n"):
            df = apply_ranking(
                df,
                metric,
                query["top_n"]
            )

        #forecast
        if query.get("forecast"):
            forecast = forecast_metric(df, metric)
            return success_response(forecast)
        
        #insight
        insight = generate_insight(df, metric)

        return success_response(
            df.to_dict(orient="records"),
            insight
        )
    except Exception as e:
        return error_response(str(e))
    