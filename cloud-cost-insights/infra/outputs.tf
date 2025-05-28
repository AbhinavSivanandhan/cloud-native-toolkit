output "lambda_name" {
  value = aws_lambda_function.cost_insights.function_name
}

output "lambda_arn" {
  value = aws_lambda_function.cost_insights.arn
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.http_api.api_endpoint
}

output "security_guard_endpoint" {
  value = "${aws_apigatewayv2_api.http_api.api_endpoint}/security-guard"
}
