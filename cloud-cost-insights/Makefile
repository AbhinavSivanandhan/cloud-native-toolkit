.PHONY: deploy destroy init plan output logs build

# Build Lambda zip packages
build:
	cd infra/lambda && bash build_lambda.sh

# Deploy full infra + update dashboard API info
deploy: build
	terraform -chdir=infra apply -auto-approve -var-file=secrets.auto.tfvars
	terraform -chdir=infra output -json > ../dashboards/cost_insights_ui/api_info.json

# Tear everything down
destroy:
	terraform -chdir=infra destroy -auto-approve -var-file=secrets.auto.tfvars

# Tail Lambda logs
logs:
	aws logs tail /aws/lambda/cloud-cost-insights --follow

# View plan
plan:
	terraform -chdir=infra plan

# Init Terraform
init:
	terraform -chdir=infra init

# Output variables
output:
	terraform -chdir=infra output
