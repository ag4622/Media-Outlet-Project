terraform {
  backend "s3" {
    bucket = "sigma-terraform-config"
    key    = "c23-alex-jess-tom"
    region = "eu-west-2"
    encrypt = true
  }
}

provider "aws" {
  region = "eu-west-2"
}

resource "aws_dynamodb_table" "trials_table" {
  name         = "c23-ClinicalTrialTracker"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "trial_id"
  range_key = "updated_at"
  
  attribute {
    name = "trial_id"
    type = "S"
  }


  attribute {
    name = "updated_at"
    type = "S"
  }

  tags = {
    Project = "c23-ClinicalTrialTracker"
  }
}