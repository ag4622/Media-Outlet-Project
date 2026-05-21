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


data "aws_ecs_cluster" "cohort_cluster" {
    cluster_name = "c23-ecs-cluster"
}

data "aws_vpc" "cohort_vpc" {
    id = "vpc-08c6b21a04bd32897"
}

data "aws_subnets" "public_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.cohort_vpc.id]
  }
}


resource "aws_security_group" "dashboard_sg" {
    name = "c23-abyssopelagic-security-group"
    vpc_id = data.aws_vpc.cohort_vpc.id
}


resource "aws_vpc_security_group_egress_rule" "allow_all_traffic_ipv4" {
    security_group_id = aws_security_group.dashboard_sg.id
    cidr_ipv4         = "0.0.0.0/0"
    ip_protocol       = "-1" # semantically equivalent to all ports
}


resource "aws_dynamodb_table" "trials_table" {
  name         = "c23-ClinicalTrialTracker"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "trial_id"
  range_key = "published_date"

  attribute {
    name = "trial_id"
    type = "S"
  }


  attribute {
    name = "published_date"
    type = "S"
  }

  tags = {
    Project = "c23-ClinicalTrialTracker"
  }
}

