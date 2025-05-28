import json
import boto3
import os
import requests

def ask_sonar(prompt: str) -> str:
    api_key = os.environ.get("SONAR_API_KEY")
    if not api_key:
        raise Exception("Missing SONAR_API_KEY in environment variables.")

    response = requests.post(
        url="https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": "You are a Terraform governance expert."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4
        },
        timeout=30
    )

    try:
        return response.json()["choices"][0]["message"]["content"]
    except Exception:
        raise Exception(f"Failed to parse Sonar response: {response.text}")

def lambda_handler(event, context):
    ec2 = boto3.client("ec2")
    instances = ec2.describe_instances(MaxResults=5)

    if not instances.get("Reservations"):
        return {
            "statusCode": 200,
            "body": json.dumps({"terraform": "No EC2 instances found."})
        }

    all_instances = []
    for res in instances["Reservations"]:
        all_instances.extend(res["Instances"])

    prompt = f"""
You are an expert in AWS Cloud Governance. Below is metadata from live EC2 instances:

{json.dumps(all_instances, indent=2, default=str)}

Please analyze them and:
- Flag missing or inconsistent tags (e.g. Name, Environment).
- Identify duplicate or similar instances (e.g. same AMI, type, purpose).
- Suggest Terraform modules to standardize configuration.
- Return clean Terraform suggestions if applicable.
- If everything looks good, say so. Do NOT return generic placeholders.
"""

    terraform_code = ask_sonar(prompt)

    return {
        "statusCode": 200,
        "body": json.dumps({"terraform": terraform_code})
    }
