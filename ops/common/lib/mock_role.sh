#! /bin/bash
 
set -e
 
eval "$(jq -r '@sh "ROLE_ARN=\(.role_arn)"')"
 
# creds=$(aws sts assume-role --role-arn $role_arn --role-session-name $USER@ --policy $POLICY_JSON | jq -r .Credentials)
creds=$(aws sts assume-role --role-arn $ROLE_ARN --role-session-name $USER@ | jq -r .Credentials)
 
cat <<-_EOT_
{
    "AWS_ACCESS_KEY_ID": "$(echo $creds | jq -r .AccessKeyId)",
    "AWS_SECRET_ACCESS_KEY": "$(echo $creds | jq -r .SecretAccessKey)",
    "AWS_SESSION_TOKEN": "$(echo $creds | jq -r .SessionToken)"
}
_EOT_

