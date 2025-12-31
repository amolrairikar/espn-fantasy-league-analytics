terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

module "app_infra" {
  source = "../common_infrastructure"

  api_key = var.api_key
  environment = var.environment
}
