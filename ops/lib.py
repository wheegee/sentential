import sys
import json
import boto3
import subprocess
from typer import echo, style, colors
from pathlib import Path
from botocore.exceptions import ClientError
from aws_lambda_powertools.utilities import parameters

# Validate AWS credentials
sts = boto3.client("sts")
try:
    sts.get_caller_identity()
except ClientError as e:
    if e.response["Error"]["Code"] == "InvalidClientTokenId":
        echo(style("Invalid AWS credentials", fg=colors.RED))
        sys.exit(1)
    else:
        echo(style(f"Identity error: {e}", fg=colors.RED))
        sys.exit(1)


def cmd(target, command):
    try:
        result = subprocess.Popen(command, cwd=target, stdout=subprocess.PIPE)
        # for line in iter(result.stdout.readline, b""):
        #     echo(line)
        if result.stderr:
            raise subprocess.CalledProcessError(
                returncode=result.returncode, cmd=result.args, stderr=result.stderr
            )
        if result.stdout:
            return result.stdout.read().decode("utf-8")
    except subprocess.CalledProcessError as e:
        return style(e, fg=colors.RED)
    except FileNotFoundError as e:
        return style(e, fg=colors.RED)


class Parameters:
    def __init__(self, kms_key_alias, prefix):
        # SSM
        self.prefix = str(Path(f"/{prefix}"))
        self.ssm_client = boto3.client("ssm")
        self.ssm_provider = parameters.SSMProvider()

        # KMS
        self.kms_key_alias = f"alias/{kms_key_alias}"
        self.kms_client = boto3.client("kms")

    def kms_key_id(self):
        kms_key_id = None
        for alias in self.kms_client.list_aliases()["Aliases"]:
            if alias["AliasName"] == self.kms_key_alias:
                kms_key_id = alias["TargetKeyId"]
        return kms_key_id

    def set(self, key, value, description="created by ops.py"):
        name = str(Path(f"{self.prefix}/{key}"))
        try:
            self.ssm_client.put_parameter(
                Name=name,
                Description=description,
                Value=value,
                Type="SecureString",
                KeyId=self.kms_key_id(),
                Overwrite=True,
                DataType="text",
            )
            return style(f"{self.prefix}/{key}: {value}", fg=colors.GREEN)
        except ClientError as e:
            return style(f"{self.prefix}/{key}: {e}", fg=colors.RED)

    def get(self, filter, decrypt=True):
        try:
            results = self.ssm_provider.get_multiple(
                path=self.prefix, decrypt=decrypt, recursive=True
            )
        except parameters.exceptions.GetParameterError as e:
            return style(f"Parameter error: {e}", fg=colors.RED)
        except ClientError as e:
            return style(f"Client error: {e}", fg=colors.RED)

        filtered = {}
        for key, value in results.items():
            if key.startswith(filter):
                filtered[key] = value
        return json.dumps(filtered, indent=2)

    def delete(self, key):
        name = str(Path(f"{self.prefix}/{key}"))
        try:
            self.ssm_client.delete_parameter(Name=name)
            return style(f"{self.prefix}/{key}: deleted", fg=colors.GREEN)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ParameterNotFound":
                return style(f"{self.prefix}/{key}: parameter not found", fg=colors.RED)
            else:
                return style(f"{self.prefix}/{key}: {e}", fg=colors.RED)


class Registry:
    def __init__(self, name):
        # ECR
        self.name = name
        self.ecr_client = boto3.client("ecr")

    def list(self):
        try:
            results = self.ecr_client.describe_images(repositoryName=self.name)[
                "imageDetails"
            ]
        except ClientError as e:
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                return style(f"{self.name}: repository not found", fg=colors.RED)
            else:
                return style(f"Client error: {e}", fg=colors.RED)
        images = []
        for image in results:
            # Could probably utilize a dataclass
            version = {
                "pushed": f"{image['imagePushedAt']}",
                "tags": image["imageTags"],
            }
            images.append(version)

        return images

    def delete(self, tag):
        try:
            self.ecr_client.describe_images(
                repositoryName=self.name, imageIds=[{"imageTag": tag}]
            )
            self.ecr_client.batch_delete_image(
                repositoryName=self.name, imageIds=[{"imageTag": tag}]
            )
            return style(f"{tag}: deleted", fg=colors.GREEN)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ImageNotFoundException":
                return style(f"{self.name}:{tag}: image not found", fg=colors.RED)
            else:
                return style(f"Client error: {e}", fg=colors.RED)


class Deploy:
    def __init__(self, kms_key_alias, prefix):
        self.prefix = prefix
        self.kms_key_alias = kms_key_alias

    def init(self, target):
        result = cmd(f"ops/{target}", ["terraform", "init"])
        if "successfully initialized" in result:
            return True
        else:
            return result

    def apply(self, target):
        result = cmd(
            f"ops/{target}",
            [
                "terraform",
                "apply",
                "--auto-approve",
                "-var",
                f"kms_key_alias={self.kms_key_alias}",
                "-var",
                f"prefix={self.prefix}",
            ],
        )
        return style(f"{target}: deployed", fg=colors.GREEN)


class Destroy:
    def __init__(self, kms_key_alias, prefix):
        self.prefix = prefix
        self.kms_key_alias = kms_key_alias

    def init(self, target):
        result = cmd(f"ops/{target}", ["terraform", "init"])
        if "successfully initialized" in result:
            return True
        else:
            return result

    def destroy(self, target):
        result = cmd(
            f"ops/{target}",
            [
                "terraform",
                "destroy",
                "--auto-approve",
                "-var",
                f"kms_key_alias={self.kms_key_alias}",
                "-var",
                f"prefix={self.prefix}",
            ],
        )
        return style(f"{target}: destroyed", fg=colors.GREEN)
