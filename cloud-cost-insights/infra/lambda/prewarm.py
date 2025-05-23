import boto3
import os
import json
from datetime import datetime, timedelta, timezone

ce = boto3.client("ce")
s3 = boto3.client("s3")

CACHE_BUCKET = os.environ.get("CACHE_BUCKET_NAME", "")
CACHE_TTL = int(os.environ.get("CACHE_TTL_MINUTES", "30"))

def cache_key_for(day):
    return f"cost_cache/DAILY/__ALL__/{day.isoformat()}.json"

def prewarm_yesterday():
    day = datetime.utcnow().date() - timedelta(days=1)
    day_str = day.isoformat()
    end_str = (day + timedelta(days=1)).isoformat()

    print(f"Prewarming cache for {day_str}...")

    try:
        response = ce.get_cost_and_usage(
            TimePeriod={"Start": day_str, "End": end_str},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        daily_results = []
        for group in response["ResultsByTime"][0].get("Groups", []):
            service = group["Keys"][0]
            cost = group["Metrics"]["UnblendedCost"]["Amount"]
            daily_results.append({
                "date": day_str,
                "service": service,
                "cost": f"${float(cost):.2f}"
            })

        if not daily_results:
            print("No cost data found.")

        if CACHE_BUCKET:
            key = cache_key_for(day)
            s3.put_object(
                Bucket=CACHE_BUCKET,
                Key=key,
                Body=json.dumps(daily_results),
                ContentType="application/json"
            )
            print(f"✅ Cached {len(daily_results)} entries to {key}")
        else:
            print("⚠️ CACHE_BUCKET not configured.")

    except Exception as e:
        print(f"❌ Error during prewarming: {e}")

def lambda_handler(event, context):
    prewarm_yesterday()
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Prewarm complete"})
    }
