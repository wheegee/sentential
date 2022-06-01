resource "null_resource" "build" {
  triggers = {
    code_change = local.code_sha
    compose_yaml = yamlencode(local.compose)
  }

  provisioner "local-exec" {
    command = "echo '${self.triggers.compose_yaml}' | docker compose -f - build"
  }
}
