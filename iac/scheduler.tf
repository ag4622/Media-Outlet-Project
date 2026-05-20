resource "aws_iam_role" "scheduler_role" {
  name = "c23-ClinicalTrialTracker-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}


resource "aws_iam_role_policy" "scheduler_policy" {
  name = "c23-ClinicalTrialTracker-scheduler-policy"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.c23_ClinicalTrialTracker_lambda.arn
      }
    ]
  })
}


resource "aws_scheduler_schedule" "eventbridge_schedule" {
  name = "c23-ClinicalTrialTracker-pipeline-schedule"

  flexible_time_window {
    mode = "OFF"
  }

  # Every 6 hours
  schedule_expression = "cron(0 */6 * * ? *)"

  target {
    arn      = aws_lambda_function.c23_ClinicalTrialTracker_lambda.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}