variable "region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name for the Lambda function"
  default     = "cloud-cost-insights"
}

variable "lambda_memory_size" {
  default = 128
}

variable "lambda_timeout" {
  default = 30
}
