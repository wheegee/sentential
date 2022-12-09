# docker-bake.hcl

variable "tag" {}
variable "repo_name" {}
variable "repo_url" {}
variable "platforms" {
    default = ["${BAKE_LOCAL_PLATFORM}"]
}

target "runtime" {
    dockerfile = "{{ paths.runtime }}"
}

target "build" {
    contexts = {
        runtime = "target:runtime"
    }
    dockerfile = "{{ paths.dockerfile }}"
    platforms = ["${BAKE_LOCAL_PLATFORM}"]
    tags = ["${repo_name}:${tag}"]
    output = ["type=docker"]
}

target "publish" {
    contexts = {
        runtime = "target:runtime"
    }
    dockerfile = "{{ paths.dockerfile }}"
    platforms = platforms
    tags = ["${repo_url}:${tag}"]
    output = ["type=image,push=true"]
}

