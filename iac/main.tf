terraform {
  backend "s3" {
    bucket = "sigma-terraform-config"
    key    = "c23-alex-jess-tom"
    region = "eu-west-2"
    encrypt = true
  }
}