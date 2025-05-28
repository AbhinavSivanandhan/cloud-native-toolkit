# Unlike inventory guard, this file runs wrapped in lambda so that it can securely access and handle information in the cloud rather than locally.

import boto3
import json
from ai.ask import ask_freeform

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

    resp = ec2.describe_security_groups()
    for sg in resp["SecurityGroups"]:
        for perm in sg.get("IpPermissions", []):
            for ip_range in perm.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0":
                    port = perm.get("FromPort")
                    if port in [22, 3389, 80, 443]:  # Common risky ports
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
        attached = iam.list_attached_user_policies(UserName=user["UserName"])

        if not mfa["MFADevices"] or any("AdministratorAccess" in p["PolicyArn"] for p in attached.get("AttachedPolicies", [])):
            risky_users.append(user["UserName"])

    return risky_users

def summarize_risks(buckets, sgs, iam_users):
    as_json = json.dumps({
        "public_s3_buckets": buckets,
        "open_security_groups": sgs,
        "risky_iam_users": iam_users
    }, indent=2)

    prompt = f"""Analyze this AWS security data:

                ```json
                {as_json}
                ```

                * Identify any critical security risks
                * Suggest specific AWS tools or best practices to mitigate them
                * Prioritize what to fix first

                Use markdown with clear headers.
                """
    return ask_freeform(prompt)

def run_security_guard():
    print("🔒 Running Security Guard Agent...")

    buckets = get_public_s3_buckets()
    sgs = get_open_security_groups()
    iam_users = get_risky_iam_users()

    print("🧠 Querying Sonar for risk summary...")
    summary = summarize_risks(buckets, sgs, iam_users)

    return {
        "summary": summary,
        "public_s3_buckets": buckets,
        "open_security_groups": sgs,
        "risky_iam_users": iam_users
    }

if __name__ == "__main__":
    result = run_security_guard()
    print("✅ Done.\n")
    print(result["summary"])
