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
  code_dir    = "${path.module}/../../app"
  gateway_dir = "${path.module}/../../gateway"
  code_sha    = sha1(join("",[ for f in fileset(local.code_dir, "**"): sha1(filebase64("${local.code_dir}/${f}"))]))

  api_name    = data.aws_ssm_parameter.name.value
  api_version = local.code_sha
  api_description = data.aws_ssm_parameter.description.value

  build_args  = {
            "API_NAME" = local.api_name
            "API_DESCRIPTION" = local.api_description
            "API_VERSION" = local.api_version
          }

  runtime_env = {
          "API_NAME" = local.api_name
          "API_DESCRIPTION" = local.api_description
          "API_VERSION" = local.api_version
          "PREFIX" = var.prefix
        }
}

variable "prefix" {
  description = "ssm prefix"
}

variable "kms_key_alias" {
  description = "kms key used to encrypt ssm parameters"
  default = "aws/ssm"
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_ecr_repository" "api" {
  name = data.aws_ssm_parameter.repository.value
}

data "aws_kms_key" "ssm" {
  key_id = "alias/${var.kms_key_alias}"
}

data "aws_ssm_parameter" "name" {
  name  = "/${var.prefix}/name"
}

data "aws_ssm_parameter" "description" {
  name = "/${var.prefix}/description"
}

data "aws_ssm_parameter" "repository" {
  name = "/${var.prefix}/repository"
}
