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

resource "aws_s3_bucket" "cost_cache" {
  bucket = "${var.project_name}-cost-cache"
  tags   = local.common_tags
}
