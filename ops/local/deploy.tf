resource "null_resource" "deploy" {
    triggers = {
      compose_yaml = yamlencode(local.compose)
      always = timestamp()
    }

    provisioner "local-exec" {
        command = "echo '${self.triggers.compose_yaml}' | docker compose -f - up -d --force-recreate"
    }

    provisioner "local-exec" {
        when = destroy
        command = "echo '${self.triggers.compose_yaml}' | docker compose -f - down -v --rmi local"
    }
}