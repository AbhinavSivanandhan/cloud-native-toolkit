data "archive_file" "lambda_zip_cost" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda_cost.zip"
}

data "archive_file" "lambda_zip_prewarm" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda_prewarm.zip"
}

data "archive_file" "lambda_zip_orphaned" {
  type        = "zip"
  source_file = "${path.module}/lambda/orphaned_resources.py"
  output_path = "${path.module}/lambda_orphaned.zip"
}
