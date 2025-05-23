import streamlit as st
import requests
import pandas as pd
import json
from pathlib import Path
from datetime import date

# Set up dashboard UI
st.set_page_config(page_title="AWS Cost Dashboard", layout="wide")
st.title("💰 AWS Cloud Cost Dashboard")

services_cache_file = Path(__file__).parent / "services_cache.json"
endpoint = ""

# Load API endpoint from Terraform output file
api_file = Path(__file__).parent / "api_info.json"
if api_file.exists():
    try:
        api_data = json.loads(api_file.read_text())
        api_base_url = api_data["api_endpoint"]["value"]
        endpoint = f"{api_base_url}/cost-insights"
    except Exception as e:
        endpoint = ""
        st.warning(f"Failed to parse API URL: {e}")
else:
    endpoint = ""
    st.warning("API endpoint not found. Run `make deploy` first.")

# Fallback default services
default_services = [
    "AWS Amplify", "AWS Cost Explorer", "AWS Lambda", "Amazon API Gateway",
    "Amazon Route 53", "Amazon Simple Storage Service", "AmazonCloudWatch",
    "EC2 - Other", "Tax"
]

# Load discovered services if available
if services_cache_file.exists():
    try:
        aws_services = json.loads(services_cache_file.read_text())
    except Exception:
        aws_services = default_services
else:
    aws_services = default_services

# Sidebar: user input
st.sidebar.header("Query Parameters")
start_date = st.sidebar.date_input("Start Date", value=date(2025, 4, 1))
end_date = st.sidebar.date_input("End Date", value=date(2025, 4, 30))
granularity = st.sidebar.selectbox("Granularity", ["DAILY", "MONTHLY"])
ignore_cache = st.sidebar.checkbox("Bypass Cache (force fresh data)", value=False)

# Use full service list for multiselect regardless of query results
selected_services = st.sidebar.multiselect("Filter by Service(s)", aws_services)

# Fetch and display data
if st.sidebar.button("Fetch Costs"):
    if not endpoint:
        st.error("API endpoint missing. Please deploy infrastructure.")
    else:
        status_msg = st.empty()
        status_msg.info("Fetching cost data...")

        payload = {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "granularity": granularity,
            "ignore_cache": ignore_cache,
        }
        if selected_services:
            payload["service"] = selected_services

        try:
            response = requests.post(endpoint, json=payload, timeout=15)
            data = response.json()

            status_msg.empty()

            if "results" not in data:
                st.error(f"API Error: {data}")
            elif not data["results"]:
                st.warning("No results returned for the selected range.")
            else:
                results = pd.DataFrame(data["results"])

                if "cost" not in results.columns:
                    st.error("Missing 'cost' in results. Check Lambda logic.")
                else:
                    results["cost"] = results["cost"].str.replace("$", "").astype(float)

                    # 🔁 Update services cache file from newly discovered services
                    discovered = sorted(set(results["service"].dropna()))
                    if discovered:
                        current_set = set(aws_services)
                        new_set = current_set.union(discovered)
                        with open(services_cache_file, "w") as f:
                            json.dump(sorted(new_set), f, indent=2)
                            aws_services = sorted(new_set)  # 🔄 Immediately update UI choices


                    st.success(f"Data loaded for {len(results)} entries")
                    st.dataframe(results)

                    # Metadata and diagnostics
                    source = data.get("source", "unknown").capitalize()
                    st.markdown(f"🔄 **Data source**: *{source}*")

                    hits = data.get("cache_hits")
                    misses = data.get("cache_misses")
                    if hits is not None and misses is not None:
                        st.markdown(f"📦 **Cache**: {hits} hit(s), {misses} miss(es)")

                    # Charts
                    st.subheader("📈 Cost Trends Over Time (in Dollars)")
                    trend_chart = results.pivot_table(index="date", columns="service", values="cost", aggfunc="sum").fillna(0)
                    st.line_chart(trend_chart)

                    st.subheader("💸 Total Cost Breakdown by Service (in Dollars)")
                    breakdown = results.groupby("service")["cost"].sum().sort_values(ascending=False)
                    st.bar_chart(breakdown)

        except Exception as e:
            status_msg.empty()
            st.exception(f"Failed to fetch or process data: {e}")
