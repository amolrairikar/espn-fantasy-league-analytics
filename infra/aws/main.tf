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
  hash_key     = "PK"
  range_key    = "SK"

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "PK" # will be of format LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season} OR LEAGUE#{league_id}#PLATFORM#{platform}
    type = "S"
  }

  attribute {
    name = "SK" # format will vary based on the type of item being stored
    type = "S"
  }

  # GSI1 is for league matchups
  attribute {
    name = "GSI1PK" # will be of format MATCHUP#{team_a}-vs-{team_b}
    type = "S"
  }

  attribute {
    name = "GSI1SK" # will be of format LEAGUE#{league_id}#SEASON#{season}#WEEK#{week}
    type = "S"
  }

  # GSI2 is for season standings
  attribute {
    name = "GSI2PK" # will be of format STANDINGS#TEAM#{team_member_id}#SEASON#{season}
    type = "S"
  }

  attribute {
    name = "GSI2SK" # will be of format LEAGUE#{league_id}#PLATFORM#{platform}
    type = "S"
  }

  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "GSI2"
    hash_key        = "GSI2PK"
    range_key       = "GSI2SK"
    projection_type = "ALL"
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

data "aws_iam_policy_document" "lambda_policy" {
  statement {
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:BatchWriteItem",
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

  statement {
    effect = "Allow"

    actions = [
      "states:StartExecution"
    ]

    resources = [
      "arn:aws:states:us-east-2:${data.aws_caller_identity.current.account_id}:stateMachine:league-onboarding"
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "states:DescribeExecution"
    ]

    resources = [
      "arn:aws:states:us-east-2:${data.aws_caller_identity.current.account_id}:execution:league-onboarding:*"
    ]
  }
}

resource "aws_iam_role_policy" "lambda_role_policy" {
  name   = "fantasy_analytics_app_lambda_access_policy"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_policy.json
}

resource "aws_iam_role_policy_attachment" "lambda_cloudwatch_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "api_lambda" {
  function_name                  = "fantasy-analytics-api-lambda"
  description                    = "Lambda function containing API for fantasy analytics app"
  role                           = aws_iam_role.lambda_role.arn
  handler                        = "api.main.handler"
  runtime                        = "python3.13"
  filename                       = "../../api/deployment_package.zip"
  source_code_hash               = filebase64sha256("../../api/deployment_package.zip")
  timeout                        = 10
  memory_size                    = 256
  reserved_concurrent_executions = 100
  environment {
    variables = {
      API_KEY        = var.api_key
      ACCOUNT_NUMBER = data.aws_caller_identity.current.account_id
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
  endpoint_configuration {
    types = ["REGIONAL"]
  }
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

# OPTIONS method for CORS preflight
resource "aws_api_gateway_method" "proxy_options" {
  rest_api_id      = aws_api_gateway_rest_api.fastapi_api.id
  resource_id      = aws_api_gateway_resource.proxy.id
  http_method      = "OPTIONS"
  authorization    = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "proxy_options_mock" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "proxy_options_response" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers"     = true
    "method.response.header.Access-Control-Allow-Methods"     = true
    "method.response.header.Access-Control-Allow-Origin"      = true
    "method.response.header.Access-Control-Allow-Credentials" = true
  }
}

resource "aws_api_gateway_integration_response" "proxy_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  status_code = aws_api_gateway_method_response.proxy_options_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers"     = "'x-api-key,Content-Type'"
    "method.response.header.Access-Control-Allow-Methods"     = "'OPTIONS,GET,POST,PUT,DELETE'"
    "method.response.header.Access-Control-Allow-Origin"      = "'http://localhost:5173'"
    "method.response.header.Access-Control-Allow-Credentials" = "'true'"
  }

  response_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
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
  name    = "react-app-api-key"
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
    limit  = 2500
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

  # Comment this part out if a redeploy is not needed
  lifecycle {
    create_before_destroy = true
  }

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

###############################################################################
####################### Onboarding Step Functions #############################
###############################################################################

resource "aws_iam_role" "step_functions_role" {
  name = "league-onboarding-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

# Policy for invoking Lambda and writing logs
resource "aws_iam_role_policy" "step_functions_policy" {
  name = "league-onboarding-sfn-policy"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.league_members_lambda.arn,
          aws_lambda_function.league_scores_lambda.arn,
          aws_lambda_function.league_standings_lambda.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_sfn_state_machine" "league_onboarding" {
  name     = "league-onboarding"
  role_arn = aws_iam_role.step_functions_role.arn

  definition = <<EOF
{
  "Comment": "Fantasy League Onboarding Workflow",
  "StartAt": "MapSeasons",
  "States": {
    "MapSeasons": {
      "Type": "Map",
      "ItemsPath": "$.seasons",
      "MaxConcurrency": 15,
      "Parameters": {
        "leagueId.$": "$.league_id",
        "platform.$": "$.platform",
        "privacy.$": "$.privacy",
        "swidCookie.$": "$.swid_cookie",
        "espnS2Cookie.$": "$.espn_s2_cookie",
        "season.$": "$$.Map.Item.Value"
      },
      "Iterator": {
        "StartAt": "FetchMembers",
        "States": {
          "FetchMembers": {
            "Type": "Task",
            "Resource": "${aws_lambda_function.league_members_lambda.arn}",
            "Retry": [
              {
                "ErrorEquals": ["States.ALL"],
                "IntervalSeconds": 2,
                "MaxAttempts": 3,
                "BackoffRate": 2.0
              }
            ],
            "ResultPath": null,
            "Next": "FetchScores"
          },
          "FetchScores": {
            "Type": "Task",
            "Resource": "${aws_lambda_function.league_scores_lambda.arn}",
            "Retry": [
              {
                "ErrorEquals": ["States.ALL"],
                "IntervalSeconds": 2,
                "MaxAttempts": 3,
                "BackoffRate": 2.0
              }
            ],
            "ResultPath": null,
            "End": true
          }
        }
      },
      "Next": "FetchStandings"
    },
    "FetchStandings": {
      "Type": "Task",
      "Resource": "${aws_lambda_function.league_standings_lambda.arn}",
      "Retry": [
        {
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 2,
          "MaxAttempts": 3,
          "BackoffRate": 2.0
        }
      ],
      "ResultPath": null,
      "End": true
    }
  }
}
EOF

  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

resource "aws_lambda_function" "league_members_lambda" {
  function_name    = "fantasy-analytics-league-members-lambda"
  description      = "Lambda function to get league member and teams information for fantasy analytics app"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.13"
  filename         = "../../lambdas/step_function_lambdas/league_members/deployment_package.zip"
  source_code_hash = filebase64sha256("../../lambdas/step_function_lambdas/league_members/deployment_package.zip")
  timeout          = 10
  memory_size      = 256
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

resource "aws_lambda_function" "league_scores_lambda" {
  function_name    = "fantasy-analytics-league-scores-lambda"
  description      = "Lambda function to get league matchup score information for fantasy analytics app"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.13"
  filename         = "../../lambdas/step_function_lambdas/league_scores/deployment_package.zip"
  source_code_hash = filebase64sha256("../../lambdas/step_function_lambdas/league_scores/deployment_package.zip")
  timeout          = 10
  memory_size      = 256
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}

resource "aws_lambda_function" "league_standings_lambda" {
  function_name    = "fantasy-analytics-league-standings-lambda"
  description      = "Lambda function to calculate league standings for fantasy analytics app"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.13"
  filename         = "../../lambdas/step_function_lambdas/league_standings/deployment_package.zip"
  source_code_hash = filebase64sha256("../../lambdas/step_function_lambdas/league_standings/deployment_package.zip")
  timeout          = 10
  memory_size      = 256
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = "PROD"
  }
}
