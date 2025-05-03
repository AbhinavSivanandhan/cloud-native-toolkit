import boto3
import json
from datetime import datetime, timedelta

def lambda_handler(event, context):
    ce = boto3.client('ce')

    today = datetime.utcnow().date()
    start = (today - timedelta(days=1)).isoformat()
    end = today.isoformat()

    response = ce.get_cost_and_usage(
        TimePeriod={'Start': start, 'End': end},
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
    )

    print("Cost Explorer Response:")
    print(json.dumps(response, indent=2))

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Cost data fetched', 'start': start, 'end': end})
    }
