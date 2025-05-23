provider "aws" {
  region = var.region
}

locals {
  common_tags = {
    Project   = "cloud-native-toolkit"
    Phase     = "cloud-cost-insights"
    Owner     = "abhinav"
    ManagedBy = "Terraform"
  }
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-policy"
  role = aws_iam_role.lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ce:GetCostAndUsage",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "s3:ListBucket"
        ],
        Resource = "arn:aws:s3:::${aws_s3_bucket.cost_cache.bucket}"
      },
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ],
        Resource = "arn:aws:s3:::${aws_s3_bucket.cost_cache.bucket}/*"
      }
    ]
  })
  # IAM Role Policies don’t support tags (skip it)
}

# For cost_insights
data "archive_file" "lambda_zip_cost" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda_cost.zip"
}

# For cache_prewarm
data "archive_file" "lambda_zip_prewarm" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda_prewarm.zip"
}

resource "aws_s3_bucket" "cost_cache" {
  bucket = "${var.project_name}-cost-cache"

  tags = local.common_tags
}

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

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}"
  retention_in_days = 7

  tags = {
    Project   = var.project_name
    Phase     = "cloud-cost-insights"
    ManagedBy = "Terraform"
    Owner     = "abhinav"
  }
}

resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id             = aws_apigatewayv2_api.http_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.cost_insights.invoke_arn
  integration_method = "POST"
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

resource "aws_lambda_function" "cache_prewarm" {
  filename         = data.archive_file.lambda_zip_prewarm.output_path
  function_name    = "cloud-cost-prewarm"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "prewarm.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256(data.archive_file.lambda_zip_prewarm.output_path)

  environment {
    variables = {
      CACHE_BUCKET_NAME     = aws_s3_bucket.cost_cache.bucket
      CACHE_TTL_MINUTES     = "1440"  # 1 day default
    }
  }

  tags = {
    Name      = "CostInsightsPrewarm"
    ManagedBy = "Terraform"
  }
}

resource "aws_cloudwatch_event_rule" "daily_prewarm" {
  name        = "daily-cost-prewarm"
  description = "Triggers daily cache prewarm for cost insights"
  schedule_expression = "cron(0 3 * * ? *)" # Every day at 3AM UTC
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
