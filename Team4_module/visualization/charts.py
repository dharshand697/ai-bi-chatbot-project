import pandas as pd
import matplotlib.pyplot as plt
import os
from visualization.config import REPORT_PATH

print("charts.py loaded")


def monthly_revenue_chart(df):
    os.makedirs(REPORT_PATH, exist_ok=True)

    # Convert date
    df['orderdate'] = pd.to_datetime(df['orderdate'])

    # Group monthly
    monthly = df.groupby(df['orderdate'].dt.to_period('M'))['sales'].sum()

    # Plot
    monthly.plot(kind='line', title="Monthly Revenue Trend")

    # Save
    file_path = os.path.join(REPORT_PATH, "1_monthly_revenue.png")
    plt.savefig(file_path)

    plt.close()

    return file_path

def country_revenue_chart(df):
    import os
    import matplotlib.pyplot as plt

    os.makedirs(REPORT_PATH, exist_ok=True)

    # Group by country
    country = df.groupby('country')['sales'].sum().sort_values(ascending=False)

    # Plot
    country.plot(kind='bar', title="Country-wise Revenue")

    # Save
    file_path = os.path.join(REPORT_PATH, "2_country_revenue.png")
    plt.savefig(file_path)

    plt.close()

    return file_path

def product_revenue_chart(df):
    import os
    import matplotlib.pyplot as plt

    os.makedirs(REPORT_PATH, exist_ok=True)

    # Group by product line
    product = df.groupby('productline')['sales'].sum().sort_values(ascending=False)

    # Plot
    product.plot(kind='bar', title="Product-wise Revenue")

    # Save
    file_path = os.path.join(REPORT_PATH, "3_product_revenue.png")
    plt.savefig(file_path)

    plt.close()

    return file_path

def top_customers_chart(df):
    import os
    import matplotlib.pyplot as plt

    os.makedirs(REPORT_PATH, exist_ok=True)

    # Top 10 customers by revenue
    customers = (
        df.groupby('customername')['sales']
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    # Plot
    customers.plot(kind='bar', title="Top 10 Customers by Revenue")

    # Save
    file_path = os.path.join(REPORT_PATH, "4_top_customers.png")
    plt.savefig(file_path)

    plt.close()

    return file_path