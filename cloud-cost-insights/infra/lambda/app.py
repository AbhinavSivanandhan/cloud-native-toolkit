import boto3
import os
import json
import hashlib
from datetime import datetime, timedelta, timezone

ce = boto3.client("ce")
s3 = boto3.client("s3")

CACHE_BUCKET = os.environ.get("CACHE_BUCKET_NAME")
CACHE_TTL = int(os.environ.get("CACHE_TTL_MINUTES", "30"))  # cache expiry in minutes

def generate_cache_key(start, end, granularity, service=None):
    base_key = f"{start}_{end}_{granularity}"
    if service:
        base_key += f"_svc_{service}"
    hash_digest = hashlib.md5(base_key.encode()).hexdigest()
    return f"cost_cache/{hash_digest}.json"

def is_cache_valid(obj):
    last_modified = obj["LastModified"]
    now = datetime.now(timezone.utc)
    age_minutes = (now - last_modified).total_seconds() / 60
    return age_minutes < CACHE_TTL

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

    cache_key = generate_cache_key(start, end, granularity, filter_service)

    # Try loading cache
    if CACHE_BUCKET:
        try:
            obj = s3.get_object(Bucket=CACHE_BUCKET, Key=cache_key)
            if is_cache_valid(obj):
                print(f"Serving from cache: {cache_key}")
                return {
                    "statusCode": 200,
                    "body": obj["Body"].read().decode("utf-8")
                }
            else:
                print("Cache expired, refetching.")
        except s3.exceptions.NoSuchKey:
            print(f"No cache found for key: {cache_key}")

    # Build filter if needed, optional filter
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

        payload = {
            "message": "Cost data fetched",
            "start": start,
            "end": end,
            "granularity": granularity,
            "results": results
        }

        # Save to cache
        if CACHE_BUCKET:
            try:
                s3.put_object(
                    Bucket=CACHE_BUCKET,
                    Key=cache_key,
                    Body=json.dumps(payload),
                    ContentType="application/json"
                )
                print(f"Cached response to {cache_key}")
            except Exception as e:
                print(f"Failed to cache: {e}")

        return {
            "statusCode": 200,
            "body": json.dumps(payload)
        }

    except Exception as e:
        print("Error fetching cost data:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
