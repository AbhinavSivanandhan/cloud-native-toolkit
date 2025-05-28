# File: cloud-cost-insights/infra/lambda/security_guard.py

import boto3
import json
import os
import sys
import requests

# Minimal client logic (self-contained in Lambda zip)
def get_public_s3_buckets():
    s3 = boto3.client("s3")
    public_buckets = []
    for bucket in s3.list_buckets()["Buckets"]:
        try:
            acl = s3.get_bucket_acl(Bucket=bucket["Name"])
            for grant in acl.get("Grants", []):
                if grant["Grantee"].get("URI", "").endswith("AllUsers"):
                    public_buckets.append(bucket["Name"])
                    break
        except Exception:
            continue
    return public_buckets

def get_open_security_groups():
    ec2 = boto3.client("ec2")
    risky_sgs = []
    for sg in ec2.describe_security_groups()["SecurityGroups"]:
        for perm in sg.get("IpPermissions", []):
            for ip_range in perm.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0":
                    port = perm.get("FromPort")
                    if port in [22, 3389, 80, 443]:
                        risky_sgs.append({
                            "GroupId": sg["GroupId"],
                            "GroupName": sg.get("GroupName"),
                            "Port": port,
                            "Protocol": perm.get("IpProtocol"),
                        })
    return risky_sgs

def get_risky_iam_users():
    iam = boto3.client("iam")
    risky_users = []
    users = iam.list_users()["Users"]
    for user in users:
        mfa = iam.list_mfa_devices(UserName=user["UserName"])
        policies = iam.list_attached_user_policies(UserName=user["UserName"])
        if not mfa["MFADevices"] or any("AdministratorAccess" in p["PolicyArn"] for p in policies["AttachedPolicies"]):
            risky_users.append(user["UserName"])
    return risky_users

def ask_freeform(prompt: str) -> str:
    import requests
    SONAR_API_KEY = os.environ.get("SONAR_API_KEY")
    if not SONAR_API_KEY:
        return "[ERROR] SONAR_API_KEY not set"

    headers = {
        "Authorization": f"Bearer {SONAR_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": "You are a trusted AWS security advisor. Be concise."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload, timeout=20)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Sonar API Error] {str(e)}"

def run_security_guard():
    buckets = get_public_s3_buckets()
    sgs = get_open_security_groups()
    iam_users = get_risky_iam_users()

    as_json = json.dumps({
        "public_s3_buckets": buckets,
        "open_security_groups": sgs,
        "risky_iam_users": iam_users
    }, indent=2)

    prompt = f"""Analyze this AWS security data:

    ```json
    {as_json}
    ```

    - Identify critical security risks
    - Suggest AWS tools or best practices
    - Prioritize what to fix first
    """
    summary = ask_freeform(prompt)
    return {
        "summary": summary,
        "public_s3_buckets": buckets,
        "open_security_groups": sgs,
        "risky_iam_users": iam_users
    }

def lambda_handler(event, context):
    try:
        output = run_security_guard()
        return {
            "statusCode": 200,
            "body": json.dumps(output)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
