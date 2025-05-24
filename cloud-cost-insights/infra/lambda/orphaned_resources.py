import boto3
import json
from datetime import datetime, timezone, timedelta

ec2 = boto3.client("ec2")

def get_unattached_volumes():
    resp = ec2.describe_volumes(Filters=[{"Name": "status", "Values": ["available"]}])
    return [
        {
            "VolumeId": v["VolumeId"],
            "Size": v["Size"],
            "CreateTime": v["CreateTime"].astimezone(timezone.utc).isoformat(),
            "AvailabilityZone": v.get("AvailabilityZone"),
        }
        for v in resp.get("Volumes", [])
    ]

def get_unassociated_eips():
    resp = ec2.describe_addresses()
    return [
        {
            "PublicIp": eip["PublicIp"],
            "AllocationId": eip.get("AllocationId"),
            "Domain": eip.get("Domain"),
        }
        for eip in resp.get("Addresses", [])
        if not eip.get("AssociationId")
    ]

def get_unused_enis():
    resp = ec2.describe_network_interfaces(Filters=[{"Name": "status", "Values": ["available"]}])
    return [
        {
            "NetworkInterfaceId": eni["NetworkInterfaceId"],
            "Description": eni.get("Description"),
            "AvailabilityZone": eni.get("AvailabilityZone"),
        }
        for eni in resp.get("NetworkInterfaces", [])
        if not eni.get("Attachment")
    ]

def lambda_handler(event, context):
    try:
        volumes = get_unattached_volumes()
        eips = get_unassociated_eips()
        enis = get_unused_enis()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "unattached_volumes": volumes,
                "unassociated_eips": eips,
                "unused_network_interfaces": enis,
            }, indent=2)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
