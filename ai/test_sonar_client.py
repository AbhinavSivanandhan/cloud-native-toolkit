from ai.sonar_client import ask_sonar
from ai.ask import (
    ask_cost_governance_summary,
    ask_freeform,
    ask_infra_risks,
    ask_cost_change_summary,
    ask_startup_plan
)

# Basic ask_sonar test
query = "Explain the impact of leaving S3 buckets public in AWS."
response = ask_sonar(query)
print("\n🔍 Direct Sonar Query:\n", response)

# --- Test: Cost governance summary
mock_cost_data = '{"AWS Lambda": "$14.20", "Amazon S3": "$3.00", "EC2 - Other": "$128.99"}'
print("\n🧾 Cost Governance Summary:")
print(ask_cost_governance_summary(mock_cost_data))

# --- Test: Freeform question
print("\n💬 Freeform Query:")
print(ask_freeform("What are the best AWS services for student startups under $100/month?"))

# --- Test: Infra risks
mock_infra_snapshot = '''
{
  "resources": [
    {"type": "S3", "name": "public-bucket", "public": true},
    {"type": "IAM", "policy": "AdministratorAccess", "attached_to": "developer-user"},
    {"type": "EC2", "port_22_open": true}
  ]
}
'''
print("\n🔐 Infrastructure Risk Analysis:")
print(ask_infra_risks(mock_infra_snapshot))

# --- Test: Cost change summary
mock_cost_before = '{"EC2": "$150", "S3": "$5", "Lambda": "$10"}'
mock_cost_after  = '{"EC2": "$90", "S3": "$15", "Lambda": "$20"}'
print("\n💰 Cost Change Summary:")
print(ask_cost_change_summary(mock_cost_before, mock_cost_after))

# --- Test: Budget-based infra plan
print("\n📦 Startup Plan ($75/month):")
print(ask_startup_plan(75))
