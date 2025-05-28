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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["💰 Cost Insights", "🧹 Resource Scanner", "🧠 AI Risk & Cost Summary", "🛡️ Security Insights", "🤖 Infra Autopilot", "📊 Governance Copilot"])

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
# ------------------------------------------
# TAB 3: AI Risk & Cost Summary
# ------------------------------------------
with tab3:
    st.subheader("🧠 AI-Powered Infra + Cost Summary")
    st.markdown("This agent summarizes risks, anomalies, and cost insights using your live AWS data.")

    if st.button("Run Inventory Agent"):
        with st.spinner("Querying AWS + Generating Sonar Summary..."):
            try:
                import sys
                import os
                root_path = Path(__file__).resolve().parent.parent.parent  # safely go up to root
                sys.path.append(str(root_path))
                from agents.inventory_guard import summarize_inventory
                result = summarize_inventory()

                st.success("Summary generated!")
                st.markdown("### 🔍 Summary")
                st.markdown(result["summary"])

                with st.expander("📦 Raw AWS Inventory"):
                    st.json(result["raw"], expanded=False)

            except Exception as e:
                st.error("Agent failed to run")
                st.exception(e)
# ------------------------------------------
# TAB 4: SECURITY INSIGHTS
# ------------------------------------------
with tab4:
    st.subheader("🛡️ Security Insights Agent")
    st.markdown("Detect risky configurations in IAM, S3, and network exposure.")

    # Derive endpoint
    security_endpoint = ""
    try:
        if api_file.exists():
            api_data = json.loads(api_file.read_text())
            api_base_url = api_data["api_endpoint"]["value"]
            security_endpoint = f"{api_base_url}/security-guard"
    except Exception as e:
        st.warning(f"Could not parse API endpoint: {e}")

    if st.button("Run Security Check"):
        if not security_endpoint:
            st.error("Security Guard API endpoint not found.")
        else:
            with st.spinner("Scanning AWS config for vulnerabilities..."):
                try:
                    sec_response = requests.post(security_endpoint, json={}, timeout=20)
                    sec_data = sec_response.json()

                    st.success("Security insights generated!")
                    # st.markdown("### 🔍 Full API Raw Response")
                    # st.json(sec_data)
                    if "summary" in sec_data:
                        st.markdown("### 🔍 AI Summary")
                        st.markdown(sec_data["summary"])
                    else:
                        st.warning("No AI summary returned. See raw response above.")

                    if sec_data.get("public_s3_buckets"):
                        st.warning(f"📂 Public S3 Buckets: {len(sec_data['public_s3_buckets'])}")
                        st.dataframe(pd.DataFrame(sec_data["public_s3_buckets"], columns=["BucketName"]))

                    if sec_data.get("open_security_groups"):
                        st.error("🚨 Open Security Groups Detected")
                        st.dataframe(pd.DataFrame(sec_data["open_security_groups"]))

                    if sec_data.get("risky_iam_users"):
                        st.warning("⚠️ IAM Users Without MFA or Admin Overexposure")
                        st.dataframe(pd.DataFrame(sec_data["risky_iam_users"], columns=["IAM Username"]))

                except Exception as e:
                    st.error("Failed to run security guard agent.")
                    st.exception(e)

# ------------------------------------------
# TAB 5: INFRA AUTOPILOT
# ------------------------------------------
with tab5:
    st.subheader("🤖 Infra Autopilot Agent")
    st.markdown("Scans AWS CloudWatch logs and suggests idle or underused infra you can pause.")

    if st.button("Run Infra Autopilot"):
        with st.spinner("Reading logs + Generating recommendations..."):
            try:
                import sys
                root_path = Path(__file__).resolve().parent.parent.parent
                sys.path.append(str(root_path))
                from agents.infra_autopilot import generate_autopilot_summary
                summaries = generate_autopilot_summary()

                if not summaries:
                    st.info("✅ No clear idle patterns detected.")
                else:
                    for group, advice in summaries:
                        st.markdown(f"### 🔍 `{group}`")
                        st.markdown(advice)

            except Exception as e:
                st.error("Autopilot Agent failed.")
                st.exception(e)

# ------------------------------------------
# TAB 6: GOVERNANCE COPILOT
# ------------------------------------------
with tab6:
    st.subheader("📊 Governance Copilot")
    st.markdown("Analyze EC2 configurations for tagging, modularity, duplication, and Terraform best practices.")

    governance_endpoint = ""
    try:
        if api_file.exists():
            api_data = json.loads(api_file.read_text())
            api_base_url = api_data["api_endpoint"]["value"]
            governance_endpoint = f"{api_base_url}/governance-copilot"
    except Exception as e:
        st.warning(f"Could not parse API endpoint: {e}")

    if st.button("Run Governance Check"):
        if not governance_endpoint:
            st.error("Missing API URL.")
        else:
            with st.spinner("Analyzing infrastructure..."):
                try:
                    resp = requests.post(governance_endpoint, json={}, timeout=30)
                    data = resp.json()
                    st.code(data.get("terraform", "No Terraform code returned."), language="hcl")
                except Exception as e:
                    st.error("Failed to run Governance Copilot.")
                    st.exception(e)
