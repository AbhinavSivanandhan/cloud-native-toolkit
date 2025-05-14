import boto3
import os
import json
from datetime import datetime, timedelta

ce = boto3.client("ce")

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    # Parse request body
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON input"})
        }

    # Handle env var with fallback and debug
    try:
        default_lookback_days = int(os.environ.get("DEFAULT_LOOKBACK_DAYS", 1))
    except ValueError:
        print("Invalid DEFAULT_LOOKBACK_DAYS env var; falling back to 1")
        default_lookback_days = 1

    # Determine query parameters
    end = body.get("end") or datetime.utcnow().date().isoformat()
    start = body.get("start") or (datetime.utcnow() - timedelta(days=default_lookback_days)).date().isoformat()
    granularity = body.get("granularity", "DAILY")
    filter_service = body.get("service")

    # Construct optional filter
    filter_block = None
    if filter_service:
        filter_block = {
            "Dimensions": {
                "Key": "SERVICE",
                "Values": [filter_service]
            }
        }

    print(f"Fetching cost data from {start} to {end}, granularity={granularity}, filter={filter_block}")

    try:
        response = ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity=granularity,
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            **({"Filter": filter_block} if filter_block else {})
        )

        # Format results
        results = []
        for time_period in response["ResultsByTime"]:
            date = time_period["TimePeriod"]["Start"]
            for group in time_period.get("Groups", []):
                service = group["Keys"][0]
                cost = group["Metrics"]["UnblendedCost"]["Amount"]
                results.append({
                    "date": date,
                    "service": service,
                    "cost": f"${float(cost):.2f}"
                })

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Cost data fetched",
                "start": start,
                "end": end,
                "granularity": granularity,
                "results": results
            })
        }

    except Exception as e:
        print("Error fetching cost data:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
