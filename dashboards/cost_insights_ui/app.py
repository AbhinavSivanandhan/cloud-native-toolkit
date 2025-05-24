import streamlit as st
import requests
import pandas as pd
import json
from pathlib import Path
from datetime import date

# UI config
st.set_page_config(page_title="AWS Cloud Dashboard", layout="wide")

# Title and layout
st.title("🧠 AWS Cloud Governance Dashboard")

# File paths
services_cache_file = Path(__file__).parent / "services_cache.json"
api_file = Path(__file__).parent / "api_info.json"

# API endpoints
endpoint = ""
orphaned_endpoint = ""

if api_file.exists():
    try:
        api_data = json.loads(api_file.read_text())
        api_base_url = api_data["api_endpoint"]["value"]
        endpoint = f"{api_base_url}/cost-insights"
        orphaned_endpoint = f"{api_base_url}/orphaned-resources"
    except Exception as e:
        st.warning(f"Failed to parse API URL: {e}")

# Fallback services list
default_services = [
    "AWS Amplify", "AWS Cost Explorer", "AWS Lambda", "Amazon API Gateway",
    "Amazon Route 53", "Amazon Simple Storage Service", "AmazonCloudWatch",
    "EC2 - Other", "Tax"
]

# Load cached/discovered services
if services_cache_file.exists():
    try:
        aws_services = json.loads(services_cache_file.read_text())
    except Exception:
        aws_services = default_services
else:
    aws_services = default_services

# Tabs
tab1, tab2 = st.tabs(["💰 Cost Insights", "🧹 Resource Scanner"])

# ------------------------------------------
# TAB 1: COST INSIGHTS
# ------------------------------------------
with tab1:
    st.subheader("💰 AWS Cost Dashboard")

    # Sidebar query inputs
    st.sidebar.header("Query Parameters")
    start_date = st.sidebar.date_input("Start Date", value=date(2025, 4, 1))
    end_date = st.sidebar.date_input("End Date", value=date(2025, 4, 30))
    granularity = st.sidebar.selectbox("Granularity", ["DAILY", "MONTHLY"])
    ignore_cache = st.sidebar.checkbox("Bypass Cache (force fresh data)", value=False)
    selected_services = st.sidebar.multiselect("Filter by Service(s)", aws_services)

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

                        # Update cache file with new services
                        discovered = sorted(set(results["service"].dropna()))
                        if discovered:
                            current_set = set(aws_services)
                            new_set = current_set.union(discovered)
                            with open(services_cache_file, "w") as f:
                                json.dump(sorted(new_set), f, indent=2)
                                aws_services = sorted(new_set)

                        st.success(f"Data loaded for {len(results)} entries")
                        st.dataframe(results)

                        source = data.get("source", "unknown").capitalize()
                        st.markdown(f"🔄 **Data source**: *{source}*")

                        hits = data.get("cache_hits")
                        misses = data.get("cache_misses")
                        if hits is not None and misses is not None:
                            st.markdown(f"📦 **Cache**: {hits} hit(s), {misses} miss(es)")

                        st.subheader("📈 Cost Trends Over Time (in Dollars)")
                        trend_chart = results.pivot_table(
                            index="date", columns="service", values="cost", aggfunc="sum"
                        ).fillna(0)
                        st.line_chart(trend_chart)

                        st.subheader("💸 Total Cost Breakdown by Service (in Dollars)")
                        breakdown = results.groupby("service")["cost"].sum().sort_values(ascending=False)
                        st.bar_chart(breakdown)

            except Exception as e:
                status_msg.empty()
                st.exception(f"Failed to fetch or process data: {e}")

# ------------------------------------------
# TAB 2: RESOURCE SCANNER
# ------------------------------------------
with tab2:
    st.subheader("🧹 Orphaned Resources Scanner")
    st.markdown("This checks for unused AWS infrastructure that may be costing you money.")

    if st.button("Scan for Orphaned Resources"):
        if not orphaned_endpoint:
            st.error("Orphaned resource endpoint missing.")
        else:
            with st.spinner("Scanning..."):
                try:
                    orphaned_response = requests.post(orphaned_endpoint, json={}, timeout=20)
                    orphaned_data = orphaned_response.json()
                    if "unattached_volumes" in orphaned_data and orphaned_data["unattached_volumes"]:
                        st.success(f"Found {len(orphaned_data['unattached_volumes'])} unattached EBS volumes")
                        orphaned_df = pd.DataFrame(orphaned_data["unattached_volumes"])
                        st.dataframe(orphaned_df)
                    else:
                        st.info("✅ No unattached EBS volumes found.")
                    if orphaned_data.get("unassociated_eips"):
                        st.warning("⚠️ Found unassociated Elastic IPs")
                        st.dataframe(pd.DataFrame(orphaned_data["unassociated_eips"]))

                    if orphaned_data.get("unused_network_interfaces"):
                        st.warning("⚠️ Found unused Network Interfaces")
                        st.dataframe(pd.DataFrame(orphaned_data["unused_network_interfaces"]))
                except Exception as e:
                    st.error("Failed to fetch orphaned resource data")
                    st.exception(e)
