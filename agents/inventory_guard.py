import os
import json
import boto3
from ai.ask import ask_cost_governance_summary, ask_freeform

# Optional: fall back to mocked infra if offline/testing
MOCK_INFRA = {
    "ec2_instances": [
        {"id": "i-abc123", "type": "t2.micro", "state": "running", "port_22_open": True},
        {"id": "i-def456", "type": "t3.medium", "state": "stopped", "port_22_open": False}
    ],
    "ebs_volumes": [
        {"id": "vol-aaa", "size": 100, "attached": True},
        {"id": "vol-bbb", "size": 50, "attached": False}
    ],
    "s3_buckets": [
        {"name": "public-data", "public": True},
        {"name": "private-logs", "public": False}
    ]
}

def fetch_live_inventory():
    try:
        ec2 = boto3.client('ec2')
        s3 = boto3.client('s3')

        # Get EC2 instance metadata
        instances = ec2.describe_instances()
        instance_data = []
        for reservation in instances["Reservations"]:
            for inst in reservation["Instances"]:
                instance_data.append({
                    "id": inst["InstanceId"],
                    "type": inst["InstanceType"],
                    "state": inst["State"]["Name"],
                    "port_22_open": check_security_group_for_ssh(inst)
                })

        # Get unattached volumes
        volumes = ec2.describe_volumes()
        volume_data = [{
            "id": v["VolumeId"],
            "size": v["Size"],
            "attached": len(v.get("Attachments", [])) > 0
        } for v in volumes["Volumes"]]

        # Check for public buckets
        buckets = s3.list_buckets()
        bucket_data = []
        for b in buckets.get("Buckets", []):
            name = b["Name"]
            is_public = is_bucket_public(s3, name)
            bucket_data.append({"name": name, "public": is_public})

        return {
            "ec2_instances": instance_data,
            "ebs_volumes": volume_data,
            "s3_buckets": bucket_data
        }

    except Exception as e:
        print(f"[Error fetching AWS data] {e}")
        return MOCK_INFRA

def check_security_group_for_ssh(instance):
    try:
        for sg in instance.get("SecurityGroups", []):
            ec2 = boto3.client('ec2')
            resp = ec2.describe_security_groups(GroupIds=[sg["GroupId"]])
            for perm in resp["SecurityGroups"][0]["IpPermissions"]:
                if perm.get("FromPort") == 22 and perm.get("ToPort") == 22:
                    return True
    except Exception:
        return False
    return False

def is_bucket_public(s3_client, bucket_name):
    try:
        acl = s3_client.get_bucket_acl(Bucket=bucket_name)
        for grant in acl["Grants"]:
            if grant["Grantee"].get("URI") == "http://acs.amazonaws.com/groups/global/AllUsers":
                return True
    except Exception:
        return False
    return False

def summarize_inventory():
    inventory = fetch_live_inventory()
    inventory_json = json.dumps(inventory, indent=2)
    summary = ask_freeform(f"Analyze this AWS inventory and identify any risks or cost issues:\n\n```json\n{inventory_json}\n```")
    return {
        "summary": summary,
        "raw": inventory  # Optionally return for frontend expansion
    }

if __name__ == "__main__":
    result = summarize_inventory()
    print("🧠 Inventory AI Summary:\n")
    print(result["summary"])
