locals {
  compose = {
    services = {
      "${var.api}" = {
        image       = "${var.api}:local"
        build       = {
          context = local.code_dir
        }
        ports       = [
          "9000:8080"
        ]
        environment = merge(data.external.lambda_role_credentials.result, {
          "API_NAME"        = var.api
          "API_VERSION"     = local.code_sha
          "API_DESCRIPTION" = var.api_description
        })
      }
      "gateway" = {
        image       = "${var.api}-gateway:local"
        build       = {
          context = local.gateway_dir
        }
        ports       = [
          "8081:8081"
        ]
        environment = merge(data.external.lambda_role_credentials.result, {
          "LAMBDA_ENDPOINT" = "http://${var.api}:8080"
        })
      }
    }
  }
}

data "external" "lambda_role_credentials" {
  program = ["bash", "${path.module}/lib/mock_role.sh"]

  query = {
    policy_json = replace(data.aws_iam_policy_document.combined.json, "\n", "")
  }
}
