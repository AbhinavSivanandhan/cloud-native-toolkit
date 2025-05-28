resource "aws_lambda_function" "security_guard" {
  function_name    = "security-guard"
  filename         = "${path.module}/lambda/lambda_security.zip"  # ✅ use your prebuilt zip
  handler          = "security_guard.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("${path.module}/lambda/lambda_security.zip")
  role             = aws_iam_role.lambda_exec_role.arn
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      SONAR_API_KEY = var.sonar_api_key
    }
  }

  tags = {
    Name      = "SecurityGuard"
    ManagedBy = "Terraform"
  }
}


resource "aws_lambda_permission" "allow_security_apigw" {
  statement_id  = "AllowSecurityAPIGWInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.security_guard.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "security_integration" {
  api_id                  = aws_apigatewayv2_api.http_api.id
  integration_type        = "AWS_PROXY"
  integration_uri         = aws_lambda_function.security_guard.invoke_arn
  integration_method      = "POST"
  payload_format_version  = "2.0"
}

resource "aws_apigatewayv2_route" "security_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /security-guard"
  target    = "integrations/${aws_apigatewayv2_integration.security_integration.id}"
}
