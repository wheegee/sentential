resource "null_resource" "build" {
    triggers = {
      code_change = local.code_sha
      compose_yaml = yamlencode(local.compose)
    }

    provisioner "local-exec" {
        command = "echo '${self.triggers.compose_yaml}' | docker compose -f - build"
    }
}

data "external" "image" {
    depends_on = [null_resource.build]
    program = ["bash", "${path.module}/lib/image.sh"]
    query = {
        image = data.aws_ecr_repository.api.repository_url
        tag = local.code_sha
    }
}