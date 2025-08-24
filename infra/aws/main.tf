terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-2"
}

resource "aws_dynamodb_table" "application_table" {
  # checkov:skip=CKV_AWS_119:Ensure DynamoDB Tables are encrypted using a KMS Customer Managed CMK
  name         = "fantasy-analytics-app-db"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "metricId"

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "metricId"
    type = "S"
  }

  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}
