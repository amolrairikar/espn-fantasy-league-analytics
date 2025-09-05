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
