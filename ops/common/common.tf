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

    compose = {
        secrets = {
          aws_creds = {
            file = "~/.aws"
          }
        }

        services = {
            "${var.api}" = {
                image = "${data.aws_ecr_repository.api.repository_url}:${local.code_sha}"
                build = {
                    context = "${path.module}/../../${var.api}"
                }
                ports = [
                  "9000:8080"
                ]
                environment = {
                    "API_NAME" = var.api
                    "API_VERSION" = local.code_sha
                    "AWS_SHARED_CREDENTIALS_FILE" = "/run/secrets/aws_creds/credentials"
                }
                secrets = [
                  "aws_creds"
                ]
            }
        }
    }
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