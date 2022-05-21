locals {
  compose = {
    services = {
      "${data.aws_ssm_parameter.name.value}" = {
        image       = "${data.aws_ecr_repository.api.repository_url}:${local.code_sha}"
        build       = {
          context = local.code_dir
          args    = local.build_args
        }
        environment = local.runtime_env
      }
    }
  }
}
