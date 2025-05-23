# generate_all_services_from_ce.py
import boto3
import json
from datetime import date

ce = boto3.client("ce")

def fetch_all_services():
    # 6 months back
    start = "2024-11-01"
    end = date.today().isoformat()

    response = ce.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
    )

    service_names = set()
    for result in response.get("ResultsByTime", []):
        for group in result.get("Groups", []):
            service = group.get("Keys", [None])[0]
            if service:
                service_names.add(service)

    return sorted(service_names)

if __name__ == "__main__":
    print("Querying AWS Cost Explorer for all services...")
    services = fetch_all_services()
    with open("services_cleaned_ce.json", "w") as f:
        json.dump(services, f, indent=2)
    print(f"Done. Retrieved {len(services)} service names.")
