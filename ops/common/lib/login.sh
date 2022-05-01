#! /bin/bash
 
set -e
 
eval "$(jq -r '@sh "ACCOUNT_ID=\(.account_id) REGION=\(.region)"')"
 
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com > /dev/null
 
cat <<-_EOT_
{
    "exit": "$?"
}
_EOT_