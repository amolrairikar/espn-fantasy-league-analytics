###############################################################################
############################### Database ######################################
###############################################################################

resource "aws_dynamodb_table" "application_table" {
  name         = var.environment == "prod" ? "fantasy-recap-app-db" : "fantasy-recap-app-db-dev"
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
    name = "GSI1SK" # will be of format LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}#WEEK#{week}
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

  # GSI3 is to get all matchups in a league for a season/week combination (is the inverse of GSI1)
  attribute {
    name = "GSI3PK" # will be of format LEAGUE#{league_id}#PLATFORM{platform}#SEASON#{season}#WEEK#{week}
    type = "S"
  }

  attribute {
    name = "GSI3SK" # will be of format MATCHUP#{team_a}-vs-{team_b}
    type = "S"
  }

  # GSI4 is to get all matchups in a league for a team
  attribute {
    name = "GSI4PK" # will be of format MATCHUP#TEAM#{team_id}
    type = "S"
  }

  attribute {
    name = "GSI4SK" # will be of format LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}#WEEK#{week}
    type = "S"
  }

  # GSI5 is to be used for bulk league deletion
  attribute {
    name = "GSI5PK" # will be of format LEAGUE#{league_id}
    type = "S"
  }

  attribute {
    name = "GSI5SK" # will be static value FOR_DELETION_USE_ONLY
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

  global_secondary_index {
    name            = "GSI3"
    hash_key        = "GSI3PK"
    range_key       = "GSI3SK"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "GSI4"
    hash_key        = "GSI4PK"
    range_key       = "GSI4SK"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "GSI5"
    hash_key        = "GSI5PK"
    range_key       = "GSI5SK"
    projection_type = "ALL"
  }

  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
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
  name               = var.environment == "prod" ? "fantasy_recap_app_lambda_role" : "fantasy_recap_app_lambda_role_dev"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
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
        aws_sfn_state_machine.league_onboarding.arn
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "states:DescribeExecution"
    ]

    resources = [
        var.environment == "prod"
            ? "arn:aws:states:us-east-1:${data.aws_caller_identity.current.account_id}:execution:league-onboarding:*"
            : "arn:aws:states:us-east-1:${data.aws_caller_identity.current.account_id}:execution:league-onboarding-dev:*"
    ]
  }
}

resource "aws_iam_role_policy" "lambda_role_policy" {
  name   = var.environment == "prod" ? "fantasy_recap_app_lambda_access_policy" : "fantasy_recap_app_lambda_access_policy_dev"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_policy.json
}

resource "aws_iam_role_policy_attachment" "lambda_cloudwatch_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "api_lambda" {
  function_name                  = var.environment == "prod" ? "fantasy-recap-api-lambda" : "fantasy-recap-api-lambda-dev"
  description                    = "Lambda function containing API for fantasy recap app"
  role                           = aws_iam_role.lambda_role.arn
  handler                        = "api.main.handler"
  runtime                        = "python3.13"
  filename                       = "../../../api/deployment_package.zip"
  source_code_hash               = filebase64sha256("../../../api/deployment_package.zip")
  timeout                        = 10
  memory_size                    = 256
  reserved_concurrent_executions = 100
  environment {
    variables = {
      API_KEY             = var.api_key
      ACCOUNT_NUMBER      = data.aws_caller_identity.current.account_id
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.application_table.name
      ONBOARDING_SFN_ARN  = aws_sfn_state_machine.league_onboarding.arn
      ENVIRONMENT         = upper(var.environment)
    }
  }
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
  }
}

resource "aws_api_gateway_rest_api" "fastapi_api" {
  name        = var.environment == "prod" ? "fantasy-recap-app-api" : "fantasy-recap-app-api-dev"
  description = "REST API for fantasy recap app using FastAPI running on Lambda"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
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
  rest_api_id       = aws_api_gateway_rest_api.fastapi_api.id
  resource_id       = aws_api_gateway_resource.proxy.id
  http_method       = aws_api_gateway_method.proxy_options.http_method
  status_code       = aws_api_gateway_method_response.proxy_options_response.status_code
  selection_pattern = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers"     = "'x-api-key,Content-Type'"
    "method.response.header.Access-Control-Allow-Methods"     = "'OPTIONS,GET,POST,PUT,PATCH,DELETE'"
    "method.response.header.Access-Control-Allow-Origin"      = "'${var.environment == "prod" ? "https://fantasy-recap.com" : "https://fantasy-recap-dev.com"}'"
    "method.response.header.Access-Control-Allow-Credentials" = "'true'"
  }

  response_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }

  # Force Terraform to wait until the integration exists
  depends_on = [
    aws_api_gateway_integration.proxy_options_mock
  ]
}

resource "aws_api_gateway_stage" "development" {
  depends_on    = [aws_cloudwatch_log_group.api_log_group]
  deployment_id = aws_api_gateway_deployment.deployment.id
  rest_api_id   = aws_api_gateway_rest_api.fastapi_api.id
  stage_name    = var.environment == "prod" ? "production" : "development"
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_log_group.arn
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
    Environment = upper(var.environment)
  }
}

resource "aws_api_gateway_method_settings" "all_endpoint_method_settings" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id
  stage_name  = aws_api_gateway_stage.development.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled    = true
    logging_level      = "INFO"
    data_trace_enabled = true
  }
}

resource "aws_api_gateway_api_key" "api_key" {
  name    = var.environment == "prod" ? "react-app-api-key" : "react-app-api-key-dev"
  enabled = true
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
  }
}

resource "aws_api_gateway_usage_plan" "usage_plan" {
  name = var.environment == "prod" ? "fantasy-recap-app-api-usage-plan" : "fantasy-recap-app-api-usage-plan-dev"

  api_stages {
    api_id = aws_api_gateway_rest_api.fastapi_api.id
    stage  = aws_api_gateway_stage.development.stage_name
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
    Environment = upper(var.environment)
  }
}

resource "aws_api_gateway_usage_plan_key" "plan_key" {
  key_id        = aws_api_gateway_api_key.api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.usage_plan.id
}

resource "aws_api_gateway_deployment" "deployment" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id

  # # Add this trigger block to force redeployment
  # triggers = {
  #   redeploy_forced = timestamp()
  # }

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

resource "aws_cloudwatch_log_group" "api_log_group" {
  name = var.environment == "prod" ? "api-gateway-execution-logs-${aws_api_gateway_rest_api.fastapi_api.id}/production" : "api-gateway-execution-logs-${aws_api_gateway_rest_api.fastapi_api.id}/development"
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
  }
}

resource "aws_iam_role" "api_gateway_cloudwatch_role" {
  name = var.environment == "prod" ? "api-gateway-cloudwatch-logs-role" : "api-gateway-cloudwatch-logs-role-dev"

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
    Environment = upper(var.environment)
  }
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch_role_attach" {
  role       = aws_iam_role.api_gateway_cloudwatch_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# ###############################################################################
# ############################### Frontend ######################################
# ###############################################################################

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "react_site" {
  bucket = var.environment == "prod" ? "${data.aws_caller_identity.current.account_id}-fantasy-recap-react-site" : "${data.aws_caller_identity.current.account_id}-fantasy-recap-react-site-dev"
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
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
  name                              = var.environment == "prod" ? "fantasy-recap-react-app-oac" : "fantasy-recap-react-app-oac-dev"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "react_distribution" {
  enabled             = true
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.react_site.bucket_regional_domain_name
    origin_id                = var.environment == "prod" ? "react-app-s3" : "react-app-s3-dev"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }

  default_cache_behavior {
    target_origin_id       = var.environment == "prod" ? "react-app-s3" : "react-app-s3-dev"
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

  aliases = [var.environment == "prod" ? "fantasy-recap.com" : "fantasy-recap-dev.com"]

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.cert_validation.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  # The custom error responses ensure on page refresh we serve from index.html
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
    Environment = upper(var.environment)
    Name        = var.environment == "prod" ? "fantasy-recap-app-cloudfront-distribution" : "fantasy-recap-app-cloudfront-distribution-dev"
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

resource "aws_route53_record" "cloudfront_alias" {
  zone_id = data.aws_route53_zone.r53_zone.zone_id
  name    = var.environment == "prod" ? "fantasy-recap.com" : "fantasy-recap-dev.com"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.react_distribution.domain_name
    zone_id                = aws_cloudfront_distribution.react_distribution.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_acm_certificate" "cert" {
  domain_name       = var.environment == "prod" ? "fantasy-recap.com" : "fantasy-recap-dev.com"
  validation_method = "DNS"

  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
  }

  lifecycle {
    create_before_destroy = true
  }
}

data "aws_route53_zone" "r53_zone" {
  name         = var.environment == "prod" ? "fantasy-recap.com" : "fantasy-recap-dev.com"
  private_zone = false
}

resource "aws_route53_record" "cert_records" {
  for_each = {
    for dvo in aws_acm_certificate.cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.r53_zone.zone_id
}

resource "aws_acm_certificate_validation" "cert_validation" {
  certificate_arn         = aws_acm_certificate.cert.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_records : record.fqdn]
}

# ###############################################################################
# ####################### Onboarding Step Functions #############################
# ###############################################################################

resource "aws_iam_role" "step_functions_role" {
  name = var.environment == "prod" ? "league-onboarding-sfn-role" : "league-onboarding-sfn-role-dev"

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
  name = var.environment == "prod" ? "league-onboarding-sfn-policy" : "league-onboarding-sfn-policy-dev"
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
          aws_lambda_function.league_draft_picks_lambda.arn,
          aws_lambda_function.league_standings_lambda.arn,
          aws_lambda_function.league_weekly_standings_lambda.arn,
          aws_lambda_function.league_records_lambda.arn
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
  name     = var.environment == "prod" ? "league-onboarding" : "league-onboarding-dev"
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
            "Next": "ParallelProcessing"
          },

          "ParallelProcessing": {
            "Type": "Parallel",
            "Branches": [
              {
                "StartAt": "FetchScores",
                "States": {
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
              {
                "StartAt": "FetchDraftPicks",
                "States": {
                  "FetchDraftPicks": {
                    "Type": "Task",
                    "Resource": "${aws_lambda_function.league_draft_picks_lambda.arn}",
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
            ],
            "Next": "ReturnInput"
          },
          "ReturnInput": {
            "Type": "Pass",
            "ResultPath": "$",
            "End": true
          }
        }
      },
      "Next": "FetchStandingsParallel"
    },
    "FetchStandingsParallel": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "FetchStandings",
          "States": {
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
        },
        {
          "StartAt": "FetchWeeklyStandings",
          "States": {
            "FetchWeeklyStandings": {
              "Type": "Task",
              "Resource": "${aws_lambda_function.league_weekly_standings_lambda.arn}",
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
        {
          "StartAt": "FetchRecords",
          "States": {
            "FetchRecords": {
              "Type": "Task",
              "Resource": "${aws_lambda_function.league_records_lambda.arn}",
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
      ],
      "ResultPath": null,
      "End": true
    }
  }
}
EOF

  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
  }
}

resource "aws_lambda_layer_version" "shared_dependencies_layer" {
  layer_name          = var.environment == "prod" ? "league_onboarding_shared_dependencies" : "league_onboarding_shared_dependencies_dev"
  description         = "Shared utility functions used by Lambda functions running in league onboarding process."
  compatible_runtimes = ["python3.13"]
  filename            = "../../../lambda_layer/deployment_package.zip"
  source_code_hash    = filebase64sha256("../../../lambda_layer/deployment_package.zip")
}

resource "aws_lambda_function" "league_members_lambda" {
  function_name    = var.environment == "prod" ? "fantasy-recap-league-members-lambda" : "fantasy-recap-league-members-lambda-dev"
  description      = "Lambda function to get league member and teams information for fantasy recap app"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.13"
  filename         = "../../../lambdas/step_function_lambdas/league_members/deployment_package.zip"
  source_code_hash = filebase64sha256("../../../lambdas/step_function_lambdas/league_members/deployment_package.zip")
  timeout          = 10
  memory_size      = 256
  layers           = [aws_lambda_layer_version.shared_dependencies_layer.arn]
  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.application_table.name
    }
  }
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
  }
}

resource "aws_lambda_function" "league_scores_lambda" {
  function_name    = var.environment == "prod" ? "fantasy-recap-league-scores-lambda" : "fantasy-recap-league-scores-lambda-dev"
  description      = "Lambda function to get league matchup score information for fantasy recap app"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.13"
  filename         = "../../../lambdas/step_function_lambdas/league_scores/deployment_package.zip"
  source_code_hash = filebase64sha256("../../../lambdas/step_function_lambdas/league_scores/deployment_package.zip")
  timeout          = 20
  memory_size      = 2048
  layers           = [aws_lambda_layer_version.shared_dependencies_layer.arn]
  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.application_table.name
    }
  }
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
  }
}

resource "aws_lambda_function" "league_standings_lambda" {
  function_name    = var.environment == "prod" ? "fantasy-recap-league-standings-lambda" : "fantasy-recap-league-standings-lambda-dev"
  description      = "Lambda function to calculate league standings for fantasy recap app"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.13"
  filename         = "../../../lambdas/step_function_lambdas/league_standings/deployment_package.zip"
  source_code_hash = filebase64sha256("../../../lambdas/step_function_lambdas/league_standings/deployment_package.zip")
  timeout          = 60
  memory_size      = 2048
  layers           = [aws_lambda_layer_version.shared_dependencies_layer.arn]
  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.application_table.name
    }
  }
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
  }
}

resource "aws_lambda_function" "league_weekly_standings_lambda" {
  function_name    = var.environment == "prod" ? "fantasy-recap-league-weekly-standings-lambda" : "fantasy-recap-league-weekly-standings-lambda-dev"
  description      = "Lambda function to calculate league weekly standings snapshot for fantasy recap app"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.13"
  filename         = "../../../lambdas/step_function_lambdas/league_weekly_standings/deployment_package.zip"
  source_code_hash = filebase64sha256("../../../lambdas/step_function_lambdas/league_weekly_standings/deployment_package.zip")
  timeout          = 60
  memory_size      = 2048
  layers           = [aws_lambda_layer_version.shared_dependencies_layer.arn]
  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.application_table.name
    }
  }
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
  }
}

resource "aws_lambda_function" "league_records_lambda" {
  function_name    = var.environment == "prod" ? "fantasy-recap-league-records-lambda" : "fantasy-recap-league-records-lambda-dev"
  description      = "Lambda function to calculate league records for fantasy recap app"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.13"
  filename         = "../../../lambdas/step_function_lambdas/league_records/deployment_package.zip"
  source_code_hash = filebase64sha256("../../../lambdas/step_function_lambdas/league_records/deployment_package.zip")
  timeout          = 60
  memory_size      = 2048
  layers           = [aws_lambda_layer_version.shared_dependencies_layer.arn]
  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.application_table.name
    }
  }
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
  }
}

resource "aws_lambda_function" "league_draft_picks_lambda" {
  function_name    = var.environment == "prod" ? "fantasy-recap-league-draft-picks-lambda" : "fantasy-recap-league-draft-picks-lambda-dev"
  description      = "Lambda function to get league draft picks for fantasy recap app"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.13"
  filename         = "../../../lambdas/step_function_lambdas/league_drafts/deployment_package.zip"
  source_code_hash = filebase64sha256("../../../lambdas/step_function_lambdas/league_drafts/deployment_package.zip")
  timeout          = 20
  memory_size      = 2048
  layers           = [aws_lambda_layer_version.shared_dependencies_layer.arn]
  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.application_table.name
    }
  }
  tags = {
    Project     = "fantasy-analytics-app"
    Environment = upper(var.environment)
  }
}
