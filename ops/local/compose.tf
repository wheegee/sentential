locals {
    compose = {
        services = {
            "${var.api}" = {
                image = "${var.api}:local"
                build = {
                    context = local.code_dir
                }
                ports = [
                    "9000:8080"
                ]
                environment = merge(data.external.lambda_role_credentials.result, {
                    "API_NAME" = var.api
                    "API_VERSION" = local.code_sha
                })
            }
        }
    }
}

data "external" "lambda_role_credentials" {
  program = ["bash", "${path.module}/lib/mock_role.sh"]

  query = {
      policy_json = replace(data.aws_iam_policy_document.ssm.json, "\n", "")
  }
}