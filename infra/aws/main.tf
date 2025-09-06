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

###############################################################################
############################### Database ######################################
###############################################################################

resource "aws_dynamodb_table" "application_table" {
  name         = "fantasy-analytics-app-db"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "leagueSeason"
  range_key    = "dataCategory"

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "leagueSeason"
    type = "S"
  }

  attribute {
    name = "dataCategory"
    type = "S"
  }

  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

###############################################################################
################################# API #########################################
###############################################################################

data "aws_iam_policy_document" "lambda_assume_role_policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = [
      "sts:AssumeRole"
    ]
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "fantasy_analytics_app_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

data "aws_iam_policy_document" "lambda_dynamodb_policy" {
  statement {
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan"
    ]

    resources = [
      aws_dynamodb_table.application_table.arn,
      "${aws_dynamodb_table.application_table.arn}/index/*"
    ]
  }
}

resource "aws_iam_role_policy" "lambda_dynamodb_role_policy" {
  name   = "fantasy_analytics_app_lambda_dynamodb_access_policy"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_dynamodb_policy.json
}

resource "aws_iam_role_policy_attachment" "lambda_cloudwatch_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "api_lambda" {
  function_name    = "fantasy-analytics-api-lambda"
  description      = "Lambda function containing API for fantasy analytics app"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.handler"
  runtime          = "python3.12"
  filename         = "../../api/deployment_package.zip"
  source_code_hash = filebase64sha256("../../api/deployment_package.zip")
  timeout          = 10
  memory_size      = 256
  environment {
    variables = {
      API_KEY = var.api_key
    }
  }
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

resource "aws_api_gateway_rest_api" "fastapi_api" {
  name        = "fantasy-analytics-app-api"
  description = "REST API for fantasy analytics app using FastAPI running on Lambda"
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

data "aws_api_gateway_resource" "root" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id
  path        = "/"
}

resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id
  parent_id   = data.aws_api_gateway_resource.root.id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.fastapi_api.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = "ANY"
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.api_lambda.invoke_arn
}

resource "aws_api_gateway_method" "proxy_any" {
  rest_api_id      = aws_api_gateway_rest_api.fastapi_api.id
  resource_id      = aws_api_gateway_resource.proxy.id
  http_method      = "ANY"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_method_response" "proxy_response" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy_any.http_method
  status_code = "200"
}

resource "aws_api_gateway_integration_response" "proxy_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy_any.http_method
  status_code = aws_api_gateway_method_response.proxy_response.status_code
}

resource "aws_api_gateway_stage" "production" {
  depends_on    = [aws_cloudwatch_log_group.api_prod_log_group]
  deployment_id = aws_api_gateway_deployment.deployment.id
  rest_api_id   = aws_api_gateway_rest_api.fastapi_api.id
  stage_name    = "production"
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_prod_log_group.arn
    format = jsonencode({
      requestId          = "$context.requestId",
      ip                 = "$context.identity.sourceIp",
      userAgent          = "$context.identity.userAgent",
      requestTime        = "$context.requestTime",
      requestTimeEpoch   = "$context.requestTimeEpoch",
      httpMethod         = "$context.httpMethod",
      resourcePath       = "$context.resourcePath",
      path               = "$context.path",
      status             = "$context.status",
      protocol           = "$context.protocol",
      responseLength     = "$context.responseLength"
      responseLatency    = "$context.responseLatency",
      integrationLatency = "$context.integrationLatency"
    })
  }
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

resource "aws_api_gateway_method_settings" "all_endpoint_method_settings" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id
  stage_name  = aws_api_gateway_stage.production.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled    = true
    logging_level      = "INFO"
    data_trace_enabled = true
  }
}

resource "aws_api_gateway_api_key" "api_key" {
  name    = "streamlit-app-api-key"
  enabled = true
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

resource "aws_api_gateway_usage_plan" "usage_plan" {
  name = "fantasy-analytics-app-api-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.fastapi_api.id
    stage  = aws_api_gateway_stage.production.stage_name
  }

  throttle_settings {
    burst_limit = 10
    rate_limit  = 5
  }

  quota_settings {
    limit  = 1000
    period = "DAY"
  }

  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

resource "aws_api_gateway_usage_plan_key" "plan_key" {
  key_id        = aws_api_gateway_api_key.api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.usage_plan.id
}

resource "aws_api_gateway_deployment" "deployment" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id

  depends_on = [
    aws_api_gateway_integration.lambda_integration
  ]
}

resource "aws_api_gateway_account" "main_account" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch_role.arn
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.fastapi_api.execution_arn}/*/*"
}

resource "aws_cloudwatch_log_group" "api_prod_log_group" {
  name = "api-gateway-execution-logs-${aws_api_gateway_rest_api.fastapi_api.id}/production"
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

resource "aws_iam_role" "api_gateway_cloudwatch_role" {
  name = "api-gateway-cloudwatch-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "apigateway.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch_role_attach" {
  role       = aws_iam_role.api_gateway_cloudwatch_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

###############################################################################
############################### Frontend ######################################
###############################################################################

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "react_site" {
  bucket = "${data.aws_caller_identity.current.account_id}-fantasy-insights-app-react-site"
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

resource "aws_s3_bucket_ownership_controls" "bucket_ownership_controls" {
  bucket = aws_s3_bucket.react_site.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "public_access_block" {
  bucket                  = aws_s3_bucket.react_site.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "versioning_config" {
  bucket = aws_s3_bucket.react_site.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "react_site_lifecycle" {
  bucket = aws_s3_bucket.react_site.id

  rule {
    id     = "delete-noncurrent-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "fantasy-insights-react-app-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "react_distribution" {
  enabled             = true
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.react_site.bucket_regional_domain_name
    origin_id                = "react-app-s3"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }

  default_cache_behavior {
    target_origin_id       = "react-app-s3"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      cookies {
        forward = "none"
      }
    }
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
    Name        = "fantasy-insights-app-cloudfront-distribution"
  }
}

resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = aws_s3_bucket.react_site.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.react_site.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.react_distribution.arn
          }
        }
      }
    ]
  })
}
