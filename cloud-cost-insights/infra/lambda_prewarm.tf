resource "aws_lambda_function" "cache_prewarm" {
  filename         = data.archive_file.lambda_zip_prewarm.output_path
  function_name    = "cloud-cost-prewarm"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "prewarm.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256(data.archive_file.lambda_zip_prewarm.output_path)

  environment {
    variables = {
      CACHE_BUCKET_NAME = aws_s3_bucket.cost_cache.bucket
      CACHE_TTL_MINUTES = "1440"
    }
  }

  tags = {
    Name      = "CostInsightsPrewarm"
    ManagedBy = "Terraform"
  }
}

resource "aws_cloudwatch_event_rule" "daily_prewarm" {
  name                = "daily-cost-prewarm"
  description         = "Triggers daily cache prewarm for cost insights"
  schedule_expression = "cron(0 3 * * ? *)"
}

resource "aws_cloudwatch_event_target" "invoke_prewarm" {
  rule      = aws_cloudwatch_event_rule.daily_prewarm.name
  target_id = "lambda"
  arn       = aws_lambda_function.cache_prewarm.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cache_prewarm.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_prewarm.arn
}
