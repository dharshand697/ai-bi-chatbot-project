from typing import Dict, Any


def generate_response(result: Dict[str, Any]) -> str:

    # ❌ Error handling
    if result.get("status") == "error":
        return f"❌ Error: {result.get('message')}"

    data    = result.get("data")
    insight = result.get("insight", "")
    intent  = result.get("intent", "")
    query   = result.get("query", {})

    if data is None:
        return "⚠️ No data found for your query."

    # ─── Scalar result (total revenue, single number) ───
    if isinstance(data, (int, float)):
        label = query.get("metric", "Value").replace("_", " ").title()
        return f"📊 **{label}: ${data:,.2f}**\n\n💡 {insight}" if insight else f"📊 **{label}: ${data:,.2f}**"

    # ─── Forecast result ───
    if isinstance(data, dict) and "forecast" in data:
        return f"📈 Forecasted Value: {data['forecast']}"

    # ─── Aggregated dict result (group_by totals) ───
    if isinstance(data, dict) and "total" in data:
        total = data["total"]
        return f"📊 **Total: ${total:,.2f}**\n\n💡 {insight}" if insight else f"📊 **Total: ${total:,.2f}**"

    # ─── List of aggregated rows (ranking/group_by results) ───
    if isinstance(data, list) and len(data) > 0:
        first = data[0]

        # Check if this is aggregated (has a summed metric) or raw rows
        keys = list(first.keys())

        # If it looks like aggregated ranking data
        if any(k in keys for k in ["sales", "revenue", "profit"]):
            metric_key = next((k for k in ["sales", "revenue", "profit"] if k in keys), keys[-1])
            group_key  = next((k for k in keys if k != metric_key), None)

            preview  = data[:10]
            response = "✅ **Top Results:**\n"

            for i, row in enumerate(preview, 1):
                group_val  = row.get(group_key, "N/A") if group_key else ""
                metric_val = row.get(metric_key, 0)

                # Format metric value
                if isinstance(metric_val, float) and metric_val > 1000:
                    metric_str = f"${metric_val:,.2f}"
                else:
                    metric_str = f"{metric_val:,.2f}"

                if group_val:
                    response += f"{i}. {group_val} — {metric_str}\n"
                else:
                    response += f"{i}. {metric_str}\n"

            if insight:
                response += f"\n💡 {insight}"

            return response

        # Raw rows fallback — summarise instead of listing
        total_sales = sum(row.get("sales", 0) for row in data)
        count       = len(data)
        return (
            f"📊 **Query returned {count} records**\n"
            f"Total Sales across results: **${total_sales:,.2f}**\n\n"
            f"💡 {insight}" if insight else
            f"📊 **Query returned {count} records**\n"
            f"Total Sales across results: **${total_sales:,.2f}**"
        )

    # ─── Generic dict result ───
    if isinstance(data, dict):
        formatted = "\n".join([f"  {k}: {v}" for k, v in data.items()])
        return f"✅ Result:\n{formatted}"

    return "⚠️ Unable to interpret the response."