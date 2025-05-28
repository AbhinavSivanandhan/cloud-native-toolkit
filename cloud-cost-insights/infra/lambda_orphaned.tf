resource "aws_lambda_function" "orphaned_resources" {
  filename         = data.archive_file.lambda_zip_orphaned.output_path
  function_name    = "orphaned-resources"
  handler          = "orphaned_resources.lambda_handler"
  runtime          = "python3.9"
  role             = aws_iam_role.lambda_exec_role.arn
  source_code_hash = filebase64sha256(data.archive_file.lambda_zip_orphaned.output_path)

  tags = {
    Name      = "OrphanedResourceScanner"
    ManagedBy = "Terraform"
  }
}

resource "aws_apigatewayv2_integration" "orphaned_integration" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.orphaned_resources.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "orphaned_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /orphaned-resources"
  target    = "integrations/${aws_apigatewayv2_integration.orphaned_integration.id}"
}

resource "aws_lambda_permission" "allow_orphaned_apigw" {
  statement_id  = "AllowOrphanedAPIGWInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.orphaned_resources.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}
