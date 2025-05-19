import boto3
import os
import json
import hashlib
from datetime import datetime, timedelta, timezone

ce = boto3.client("ce")
s3 = boto3.client("s3")

CACHE_BUCKET = os.environ.get("CACHE_BUCKET_NAME")
CACHE_TTL = int(os.environ.get("CACHE_TTL_MINUTES", "30"))

def includes_today(start_str, end_str):
    today = datetime.utcnow().date()
    start_date = datetime.fromisoformat(start_str).date()
    end_date = datetime.fromisoformat(end_str).date()
    return start_date <= today <= end_date

def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)

def cache_key_for(day, granularity, service):
    safe_service = service if service else "__ALL__"
    return f"cost_cache/{granularity}/{safe_service}/{day.isoformat()}.json"

def is_cache_valid(obj):
    last_modified = obj["LastModified"]
    now = datetime.now(timezone.utc)
    age_minutes = (now - last_modified).total_seconds() / 60
    return age_minutes < CACHE_TTL

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON input"})}

    try:
        default_lookback_days = int(os.environ.get("DEFAULT_LOOKBACK_DAYS", 1))
    except ValueError:
        default_lookback_days = 1

    end_str = body.get("end") or datetime.utcnow().date().isoformat()
    start_str = body.get("start") or (datetime.utcnow() - timedelta(days=default_lookback_days)).date().isoformat()
    granularity = body.get("granularity", "DAILY")
    filter_service = body.get("service")
    ignore_cache = body.get("ignore_cache", False)

    start_date = datetime.fromisoformat(start_str).date()
    end_date = datetime.fromisoformat(end_str).date()
    include_today = includes_today(start_str, end_str)

    results = []
    uncached_days = []

    # Try loading cached data per day
    for day in daterange(start_date, end_date):
        key = cache_key_for(day, granularity, filter_service)
        if CACHE_BUCKET and not ignore_cache and not (include_today and day == datetime.utcnow().date()):
            try:
                obj = s3.get_object(Bucket=CACHE_BUCKET, Key=key)
                if is_cache_valid(obj):
                    cached = json.loads(obj["Body"].read())
                    results.extend(cached)
                    print(f"Loaded from cache: {key}")
                    continue
                else:
                    print(f"Expired cache: {key}")
            except s3.exceptions.NoSuchKey:
                print(f"No cache: {key}")
        uncached_days.append(day)

    # Fetch fresh data for uncached days
    if uncached_days:
        for day in uncached_days:
            day_str = day.isoformat()
            try:
                response = ce.get_cost_and_usage(
                    TimePeriod={"Start": day_str, "End": (day + timedelta(days=1)).isoformat()}, #adding 1 day only when checking single day ranges
                    Granularity=granularity,
                    Metrics=["UnblendedCost"],
                    GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
                    **({"Filter": {
                        "Dimensions": {
                            "Key": "SERVICE",
                            "Values": [filter_service]
                        }
                    }} if filter_service else {})
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

                results.extend(daily_results)

                # Cache it
                if CACHE_BUCKET:
                    s3.put_object(
                        Bucket=CACHE_BUCKET,
                        Key=cache_key_for(day, granularity, filter_service),
                        Body=json.dumps(daily_results),
                        ContentType="application/json"
                    )
                    print(f"Cached: {cache_key_for(day, granularity, filter_service)}")

            except Exception as e:
                print(f"Error fetching data for {day_str}: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Cost data fetched",
            "start": start_str,
            "end": end_str,
            "granularity": granularity,
            "results": results
        })
    }
