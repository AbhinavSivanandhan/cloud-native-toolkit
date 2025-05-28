resource "aws_lambda_function" "governance_copilot" {
  function_name    = "governance-copilot"
  filename         = "${path.module}/lambda/lambda_governance.zip"
  handler          = "governance_copilot.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("${path.module}/lambda/lambda_governance.zip")
  role             = aws_iam_role.lambda_exec_role.arn
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      SONAR_API_KEY = var.sonar_api_key
    }
  }

  tags = {
    Name      = "GovernanceCopilot"
    ManagedBy = "Terraform"
  }
}

resource "aws_lambda_permission" "allow_governance_apigw" {
  statement_id  = "AllowGovernanceCopilotAPIGWInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.governance_copilot.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "governance_integration" {
  api_id                  = aws_apigatewayv2_api.http_api.id
  integration_type        = "AWS_PROXY"
  integration_uri         = aws_lambda_function.governance_copilot.invoke_arn
  integration_method      = "POST"
  payload_format_version  = "2.0"
}

resource "aws_apigatewayv2_route" "governance_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /governance-copilot"
  target    = "integrations/${aws_apigatewayv2_integration.governance_integration.id}"
}
