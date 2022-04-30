data "external" "login" {
    program = ["bash", "${path.module}/lib/login.sh"]
    query = {
        region = data.aws_region.current.name
        account_id = data.aws_caller_identity.current.account_id
    }
}

resource "null_resource" "release" {
    triggers = {
      code_sha = local.code_sha
      always = timestamp()
    }

    depends_on = [null_resource.build, data.external.login]

    provisioner "local-exec" {
        command = "echo '${yamlencode(local.compose)}' | docker compose -f - push"
    }
}