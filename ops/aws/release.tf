data "external" "login" {
  program = ["bash", "${path.module}/lib/login.sh"]
  query   = {
      region     = data.aws_region.current.name
      account_id = data.aws_caller_identity.current.account_id
  }
}

resource "null_resource" "release" {
  depends_on = [null_resource.build, data.external.login]

  triggers   = {
    code_change  = local.code_sha
    compose_yaml = yamlencode(local.compose)
  }

  provisioner "local-exec" {
    command = "echo '${self.triggers.compose_yaml}' | docker compose -f - push"
  }
}
