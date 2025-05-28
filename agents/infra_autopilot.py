# File: agents/infra_autopilot.py
import boto3
import datetime
from ai.sonar_client import ask_sonar

def get_log_groups(prefixes=None):
    logs = boto3.client("logs")
    paginator = logs.get_paginator("describe_log_groups")
    groups = []
    for page in paginator.paginate():
        for group in page["logGroups"]:
            name = group["logGroupName"]
            if not prefixes or any(p in name for p in prefixes):
                groups.append(name)
    return groups

def sample_logs(log_group, hours=48, limit=100):
    logs = boto3.client("logs")
    now = int(datetime.datetime.utcnow().timestamp() * 1000)
    past = now - hours * 3600 * 1000

    try:
        streams = logs.describe_log_streams(logGroupName=log_group, orderBy="LastEventTime", descending=True)["logStreams"]
        events = []
        for stream in streams[:2]:  # sample 2 streams max
            response = logs.get_log_events(
                logGroupName=log_group,
                logStreamName=stream["logStreamName"],
                startTime=past,
                endTime=now,
                limit=limit,
                startFromHead=False
            )
            events.extend(e["message"] for e in response["events"])
        return events
    except Exception as e:
        print(f"❌ Failed for {log_group}: {e}")
        return []

def generate_autopilot_summary():
    log_groups = get_log_groups(["/aws/lambda/", "/aws/ec2/", "/aws/rds/"])
    summaries = []

    for group in log_groups:
        print(f"🔍 Analyzing {group}...")
        logs = sample_logs(group)
        if not logs:
            continue

        prompt = f"""
You're an AWS optimization agent. Given the logs below, summarize the activity and suggest if this service is underutilized and can be paused, scaled down, or optimized:

Logs:
{'\n'.join(logs[:50])}
"""
        summary = ask_sonar(prompt)
        summaries.append((group, summary))

    return summaries
