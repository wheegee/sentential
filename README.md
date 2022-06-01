# sentential

![CI](https://github.com/bkeane/sentential/actions/workflows/main.yml/badge.svg)

## Requirements

### ECR repository

```sh
aws ecr create-repository \
  --region <region> \
  --image-scanning-configuration scanOnPush=true \
  --repository-name <app_name>
```

### Auth0

In your Auth0 tenant, create a `Custom API`, and the populate the following _secure_ SSM parameters in AWS:
- `/<app_name>/domain`
- `/<app_name>/audience`
  - Usually the `Identifier` for the API
### KMS key

If needed, create a KMS key and alias:
```sh
KEYID=$(aws kms create-key | jq -r '.KeyMetadata.KeyId')
aws kms create-alias \
  --alias-name alias/<key_name> \
  --target-key-id $KEYID
```

## Setup

Install dependencies:
```sh
pip install -r requirements.txt
```

Set SSM parameter prefix and KMS key alias:
```sh
export KMS_KEY_ALIAS=<kms_key_alias>
export PREFIX=<ssm_parameter_prefix>
```

Initialize API:
```sh
./ops.py init
```

Manage parameters:
```sh
./ops.py params set <key> <value>
./ops.py params get
./ops.py params delete <key>
```

Deploy API:
```sh
./ops.py deploy <local/aws>
```

Destroy API:
```sh
./ops.py destroy <local/aws>
```

## Project structure 

- `ops/local` - Local Lambda environment via Terraform
- `ops/aws` - AWS Lambda environment and URL via Terraform
- `app/src` - `python3 main.py` runs application locally
- `gateway/src` - `python3 main.py` runs Lambda gateway locally
