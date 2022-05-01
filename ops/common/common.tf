terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "4.10.0"
    }
  }
}

provider "aws" {}

locals {
    code_dir = "${path.module}/../../${var.api}"
    code_sha = sha1(join("",[ for f in fileset(local.code_dir, "**"): sha1(filebase64("${local.code_dir}/${f}"))]))
}

variable "api" {
  description = "the name of the api to deploy"
  default = "kaixo"
}

variable "kms_key_alias" {
  description = "kms key used to encrypt ssm parameters (default follows chamber default config)"
  default = "parameter_store_key"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

data "aws_ecr_repository" "api" {
  name = var.api
}

data "aws_kms_key" "ssm" {
  key_id = "alias/${var.kms_key_alias}"
}