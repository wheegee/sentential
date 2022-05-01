#! /bin/bash
 
set -e
 
eval "$(jq -r '@sh "POLICY_JSON=\(.policy_json)"')"
 
creds=$(aws sts get-federation-token --name $USER --policy "$POLICY_JSON" | jq -r .Credentials)

cat <<-_EOT_
{
    "AWS_ACCESS_KEY_ID": "$(echo $creds | jq -r .AccessKeyId)",
    "AWS_SECRET_ACCESS_KEY": "$(echo $creds | jq -r .SecretAccessKey)",
    "AWS_SESSION_TOKEN": "$(echo $creds | jq -r .SessionToken)",
    "CMD": "$cmd"
}
_EOT_

