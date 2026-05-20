resource "aws_iam_role" "c23_etl_lambda_role" {
  name = "c23-ClinicalTrialTracker-etl-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}


resource "aws_iam_policy" "dynamodb_policy" {
  name = "c23-ClinicalTrialTracker-dynamodb-policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem"
        ],
        Resource = aws_dynamodb_table.trials_table.arn
      }
    ]
  })
}


resource "aws_iam_policy" "bedrock_policy" {
  name = "c23-ClinicalTrialTracker-bedrock-policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "bedrock:InvokeModel"
        ],
        Resource = "*"
      }
    ]
  })
}


resource "aws_iam_policy" "lambda_logs_policy" {
  name = "c23-ClinicalTrialTracker-logs-policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      }
    ]
  })
}



resource "aws_iam_role_policy_attachment" "attach_dynamodb_policy" {
  role       = aws_iam_role.c23_etl_lambda_role.name
  policy_arn = aws_iam_policy.dynamodb_policy.arn
}


resource "aws_iam_role_policy_attachment" "attach_bedrock_policy" {
  role       = aws_iam_role.c23_etl_lambda_role.name
  policy_arn = aws_iam_policy.bedrock_policy.arn
}


resource "aws_iam_role_policy_attachment" "attach_logs_policy" {
  role       = aws_iam_role.c23_etl_lambda_role.name
  policy_arn = aws_iam_policy.lambda_logs_policy.arn
}


resource "aws_ecr_repository" "lambda_etl_ecr" {
  name                 = "c23-abyssopelagic-lambda-ecr"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
