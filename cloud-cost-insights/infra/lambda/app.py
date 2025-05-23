import boto3
import os
import json
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

def cache_key_for(day, granularity):
    # We continue to key the cache solely by day, granularity, and a literal __ALL__
    # (i.e. this cache file contains the full day's cost data, not partitioned by service)
    return f"cost_cache/{granularity}/__ALL__/{day.isoformat()}.json"

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
    ignore_cache = body.get("ignore_cache", False)

    # Accept service filter as a string or list; we do not change the cache key.
    raw_services = body.get("service")
    service_list = []
    if isinstance(raw_services, str):
        service_list = [raw_services]
    elif isinstance(raw_services, list):
        service_list = raw_services

    start_date = datetime.fromisoformat(start_str).date()
    end_date = datetime.fromisoformat(end_str).date()
    include_today = includes_today(start_str, end_str)

    results = []
    uncached_days = []
    all_cached = True
    cache_hits = 0
    cache_misses = 0

    # Loop over each day in the date range
    for day in daterange(start_date, end_date):
        key = cache_key_for(day, granularity)
        should_check_cache = CACHE_BUCKET and not ignore_cache and not (include_today and day == datetime.utcnow().date())
        if should_check_cache:
            try:
                obj = s3.get_object(Bucket=CACHE_BUCKET, Key=key)
                if is_cache_valid(obj):
                    cached = json.loads(obj["Body"].read())
                    # When filtering, do it in-memory on the cached daily data.
                    filtered = [entry for entry in cached if not service_list or entry["service"] in service_list]
                    results.extend(filtered)
                    cache_hits += 1
                    print(f"Loaded from cache: {key}")
                    continue
                else:
                    print(f"Expired cache: {key}")
            except s3.exceptions.NoSuchKey:
                print(f"No cache: {key}")
        cache_misses += 1
        all_cached = False
        uncached_days.append(day)

    # For all days that weren’t served from cache, fetch fresh data
    for day in uncached_days:
        day_str = day.isoformat()
        try:
            # Build filter: note that if service_list is empty, no filter is applied.
            filter_block = None
            if service_list:
                # Allow multiple values:
                filter_block = {
                    "Dimensions": {
                        "Key": "SERVICE",
                        "Values": service_list if isinstance(service_list, list) else [service_list]
                    }
                }
            response = ce.get_cost_and_usage(
                TimePeriod={"Start": day_str, "End": (day + timedelta(days=1)).isoformat()},
                Granularity=granularity,
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
                **({"Filter": filter_block} if filter_block else {})
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
            if CACHE_BUCKET:
                try:
                    s3.put_object(
                        Bucket=CACHE_BUCKET,
                        Key=cache_key_for(day, granularity),
                        Body=json.dumps(daily_results),
                        ContentType="application/json"
                    )
                    print(f"Cached: {cache_key_for(day, granularity)}")
                except Exception as e:
                    print(f"Failed to cache: {e}")
        except Exception as e:
            print(f"Error fetching data for {day_str}: {e}")

    source = "cache" if all_cached else ("fresh" if cache_hits == 0 else "mixed")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Cost data fetched",
            "start": start_str,
            "end": end_str,
            "granularity": granularity,
            "results": results,
            "source": source,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "services_requested": service_list
        })
    }
