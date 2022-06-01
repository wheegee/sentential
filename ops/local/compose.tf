locals {
  compose = {
    services = {
      "${data.aws_ssm_parameter.name.value}" = {
        image       = "${data.aws_ssm_parameter.name.value}:local"
        build       = {
          context = local.code_dir
          args    = local.build_args
        }
        ports       = [
          "9000:8080"
        ]
        environment = merge(data.external.lambda_role_credentials.result, 
                            local.runtime_env,
                            { "AWS_DEFAULT_REGION" = data.aws_region.current.name })
      }
      
      "gateway" = {
        image       = "${data.aws_ssm_parameter.name.value}-gateway:local"
        build       = {
          context = local.gateway_dir
        }
        ports       = [
          "8080:8080"
        ]
        environment = merge(data.external.lambda_role_credentials.result, {
          "LAMBDA_ENDPOINT" = "http://${data.aws_ssm_parameter.name.value}:8080"
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
