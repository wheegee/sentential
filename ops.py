#!/usr/bin/env python3

import json
import boto3
import typer
from typing import Optional
from aws_lambda_powertools.utilities import parameters
from pathlib import Path


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
        self.ssm_client.put_parameter(
            Name=name,
            Description=description,
            Value=value,
            Type="SecureString",
            KeyId=self.kms_key_id(),
            Overwrite=True,
            DataType="text",
        )

    def get(self, filter="", decrypt=True):
        results = self.ssm_provider.get_multiple(
            path=self.prefix, decrypt=decrypt, recursive=True
        )
        filtered = {}
        for key, value in results.items():
            if key.startswith(filter):
                filtered[key] = value
        return filtered

    def delete(self, key):
        name = str(Path(f"{self.prefix}/{key}"))
        self.ssm_client.delete_parameter(Name=name)


cli = typer.Typer()
params = typer.Typer()
cli.add_typer(params, name="params", help="manage SSM parameters")


@cli.command()
def init(
    kms_key_alias: Optional[str] = typer.Option("aws/ssm", envvar="KMS_KEY_ALIAS"),
    prefix: str = typer.Option(..., envvar="PREFIX"),
):
    """
    initialize API
    """
    api_name = typer.prompt("API name")
    api_description = typer.prompt("Description")
    api_repository = typer.prompt("Repository")

    Parameters(kms_key_alias, prefix).set("name", api_name)
    Parameters(kms_key_alias, prefix).set("description", api_description)
    Parameters(kms_key_alias, prefix).set("repository", api_repository)

    typer.echo(typer.style(f"{api_name} initialized", fg=typer.colors.GREEN))


@params.command()
def set(
    key: str,
    value: str,
    kms_key_alias: Optional[str] = typer.Option("aws/ssm", envvar="KMS_KEY_ALIAS"),
    prefix: str = typer.Option(..., envvar="PREFIX"),
):
    """
    set a parameter in SSM
    """
    Parameters(kms_key_alias, f"{prefix}/runtime/").set(key, value)

    typer.echo(typer.style(f"{prefix}/runtime/{key} == {value}", fg=typer.colors.GREEN))


@params.command()
def get(
    kms_key_alias: str = typer.Option("aws/ssm", envvar="KMS_KEY_ALIAS"),
    prefix: str = typer.Option(..., envvar="PREFIX"),
):
    """
    read parameters from SSM
    """
    typer.echo(json.dumps(Parameters(kms_key_alias, prefix).get(), indent=2))


@params.command()
def delete(
    key: str,
    kms_key_alias: str = typer.Option("aws/ssm", envvar="KMS_KEY_ALIAS"),
    prefix: str = typer.Option(..., envvar="PREFIX"),
):
    """
    delete a parameter from SSM
    """
    Parameters(kms_key_alias, f"{prefix}/runtime/").delete(key)

    typer.echo(typer.style(f"{prefix}/runtime/{key} deleted", fg=typer.colors.GREEN))


if __name__ == "__main__":
    cli()
