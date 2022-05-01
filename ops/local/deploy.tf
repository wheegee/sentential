resource "null_resource" "deploy" {
    depends_on = [ null_resource.build ]

    triggers = {
      code_change = local.code_sha
      compose_yaml = yamlencode(local.compose)
      always = timestamp()
    }

    provisioner "local-exec" {
        command = "echo '${self.triggers.compose_yaml}' | docker compose -f - up -d --force-recreate"
    }

    provisioner "local-exec" {
        when = destroy
        command = "echo '${self.triggers.compose_yaml}' | docker compose -f - down -v"
    }
}