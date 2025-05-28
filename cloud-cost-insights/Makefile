deploy:
	cd infra && terraform apply -auto-approve -var-file=secrets.auto.tfvars
	terraform -chdir=infra output -json > ../dashboards/cost_insights_ui/api_info.json

destroy:
	cd infra && terraform destroy -auto-approve -var-file=secrets.auto.tfvars

logs:
	aws logs tail /aws/lambda/cloud-cost-insights --follow

plan:
	cd infra && terraform plan

init:
	cd infra && terraform init

output:
	cd infra && terraform output
