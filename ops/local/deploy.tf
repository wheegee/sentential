resource "null_resource" "deploy" {
  triggers = {
    compose_yaml = yamlencode(local.compose)
    always       = timestamp()
  }

  provisioner "local-exec" {
    command = <<-EOT
    echo '${self.triggers.compose_yaml}' | docker-compose -f - build && \
      echo '${self.triggers.compose_yaml}' | docker compose -f - up -d --force-recreate
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "echo '${self.triggers.compose_yaml}' | docker compose -f - down -v --rmi local"
  }
}
