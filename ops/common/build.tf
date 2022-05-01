resource "null_resource" "build" {
    triggers = {
      code_change = local.code_sha
    }

    provisioner "local-exec" {
        command = "echo '${yamlencode(local.compose)}' | docker compose -f - build"
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