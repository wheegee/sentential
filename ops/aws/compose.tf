locals {
    compose = {
        services = {
            "${var.api}" = {
                image = "${data.aws_ecr_repository.api.repository_url}:${local.code_sha}"
                build = {
                    context = local.code_dir
                }
                environment = {
                    "API_NAME" = var.api
                    "API_VERSION" = local.code_sha
                }
            }
        }
    }
}
