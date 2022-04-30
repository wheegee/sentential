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
    code_dir = "${path.module}/../${var.api}"
    code_sha = sha1(join("",[ for f in fileset(local.code_dir, "**"): sha1(filebase64("${local.code_dir}/${f}"))]))

    compose = {
        services = {
            "${var.api}" = {
                image = "${data.aws_ecr_repository.api.repository_url}:${local.code_sha}"
                  # image = "kaixo:latest"
                build = {
                    context = "${path.module}/../${var.api}"
                }
                environment = {
                    "API_NAME" = var.api
                    "API_VERSION" = local.code_sha
                }
            }
        }
    }
}

variable "api" {
  description = "the name of the api to deploy"
  default = "kaixo"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_ecr_repository" "api" {
  name = var.api
}