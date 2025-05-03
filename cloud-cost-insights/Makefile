deploy:
	cd infra && terraform apply -auto-approve

destroy:
	cd infra && terraform destroy -auto-approve

logs:
	aws logs tail /aws/lambda/cloud-cost-insights --follow

plan:
	cd infra && terraform plan

init:
	cd infra && terraform init

output:
	cd infra && terraform output
