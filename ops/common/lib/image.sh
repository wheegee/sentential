#! /bin/bash
 
eval "$(jq -r '@sh "IMAGE=\(.image) TAG=\(.tag)"')"
 
entrypoint=$(docker image inspect -f '{{ (index (index .Config.Entrypoint) 0) }}' $IMAGE:$TAG)
command=$(docker image inspect -f '{{ (index (index .Config.Cmd) 0) }}' $IMAGE:$TAG)
 
cat <<-_EOT_
{
    "command": "$command",
    "entrypoint": "$entrypoint"
}
_EOT_