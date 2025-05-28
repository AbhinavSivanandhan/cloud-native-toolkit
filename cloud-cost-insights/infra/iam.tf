resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = { Service = "lambda.amazonaws.com" },
        Action    = "sts:AssumeRole"
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
      # Logging + Cost Explorer + EC2 permissions
      {
        Effect = "Allow",
        Action = [
          "ce:GetCostAndUsage",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "ec2:DescribeVolumes",
          "ec2:DescribeAddresses",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeSecurityGroups"
        ],
        Resource = "*"
      },

      # S3 access for security scan and bucket usage
      {
        Effect = "Allow",
        Action = [
          "s3:ListAllMyBuckets",
          "s3:GetBucketAcl",
          "s3:ListBucket"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ],
        Resource = "arn:aws:s3:::${aws_s3_bucket.cost_cache.bucket}/*"
      },

      # IAM introspection for risky users
      {
        Effect = "Allow",
        Action = [
          "iam:ListUsers",
          "iam:ListAttachedUserPolicies",
          "iam:ListMFADevices"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "governance_copilot_policy" {
  name   = "governance-copilot-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "EC2Access",
        Effect = "Allow",
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeTags",
          "ec2:DescribeSecurityGroups"
        ],
        Resource = "*"
      },
      {
        Sid    = "IAMAccess",
        Effect = "Allow",
        Action = [
          "iam:ListRoles"
        ],
        Resource = "*"
      },
      {
        Sid    = "S3Access",
        Effect = "Allow",
        Action = [
          "s3:ListAllMyBuckets",
          "s3:GetBucketTagging"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "governance_copilot_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.governance_copilot_policy.arn
}
