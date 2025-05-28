resource "aws_lambda_function" "cost_insights" {
  function_name    = var.project_name
  handler          = "app.lambda_handler"
  runtime          = "python3.9"
  filename         = data.archive_file.lambda_zip_cost.output_path
  source_code_hash = filebase64sha256(data.archive_file.lambda_zip_cost.output_path)
  role             = aws_iam_role.lambda_exec_role.arn
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size

  environment {
    variables = {
      DEFAULT_LOOKBACK_DAYS = "3"
      CACHE_BUCKET_NAME     = aws_s3_bucket.cost_cache.bucket
    }
  }

  tags = local.common_tags
}

resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.cost_insights.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /cost-insights"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "allow_apigw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_insights.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}
