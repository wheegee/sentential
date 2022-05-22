#!/usr/bin/env python3

import typer
from typing import Optional

from ops.lib import Parameters, Registry, Deploy, Destroy


cli = typer.Typer()
params = typer.Typer()
registry = typer.Typer()
cli.add_typer(params, name="params", help="manage SSM parameters")
cli.add_typer(registry, name="registry", help="manage image registry")


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

    typer.echo(Parameters(kms_key_alias, prefix).set("name", api_name))
    typer.echo(Parameters(kms_key_alias, prefix).set("description", api_description))
    typer.echo(Parameters(kms_key_alias, prefix).set("repository", api_repository))

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
    typer.echo(Parameters(kms_key_alias, f"{prefix}/runtime/").set(key, value))


@params.command()
def get(
    filter: str = typer.Argument(""),
    kms_key_alias: str = typer.Option("aws/ssm", envvar="KMS_KEY_ALIAS"),
    prefix: str = typer.Option(..., envvar="PREFIX"),
):
    """
    read parameters from SSM
    """
    typer.echo(Parameters(kms_key_alias, prefix).get(filter))


@params.command()
def delete(
    key: str,
    kms_key_alias: str = typer.Option("aws/ssm", envvar="KMS_KEY_ALIAS"),
    prefix: str = typer.Option(..., envvar="PREFIX"),
):
    """
    delete a parameter from SSM
    """
    typer.echo(Parameters(kms_key_alias, f"{prefix}/runtime/").delete(key))


@registry.command()
def list(
    kms_key_alias: str = typer.Option("aws/ssm", envvar="KMS_KEY_ALIAS"),
    prefix: str = typer.Option(..., envvar="PREFIX"),
):
    """
    list images in registry
    """
    results = Parameters(kms_key_alias, prefix).get("name")
    for key, value in results.items():
        if key == "name":
            typer.echo(typer.style(f"{value} versions:", fg=typer.colors.GREEN))
            for version in Registry(value).list():
                typer.echo(version["pushed"])
                for tag in version["tags"]:
                    typer.echo(typer.style(f"   {tag}", fg=typer.colors.BLUE))


@registry.command()
def delete(
    tag: str,
    kms_key_alias: str = typer.Option("aws/ssm", envvar="KMS_KEY_ALIAS"),
    prefix: str = typer.Option(..., envvar="PREFIX"),
):
    """
    delete image(s) in registry
    """
    results = Parameters(kms_key_alias, prefix).get("name")
    for key, value in results.items():
        if key == "name":
            typer.echo(Registry(value).delete(tag))


@cli.command()
def deploy(
    target: str = typer.Argument(...),
    kms_key_alias: str = typer.Option("aws/ssm", envvar="KMS_KEY_ALIAS"),
    prefix: str = typer.Option(..., envvar="PREFIX"),
):
    """
    deploy API at given target
    """
    init = Deploy(kms_key_alias, prefix).init(target)
    if init:
        typer.echo(Deploy(kms_key_alias, prefix).apply(target))
    else:
        typer.echo(init)


@cli.command()
def destroy(
    target: str = typer.Argument(...),
    kms_key_alias: str = typer.Option("aws/ssm", envvar="KMS_KEY_ALIAS"),
    prefix: str = typer.Option(..., envvar="PREFIX"),
):
    """
    destroy API at given target
    """
    init = Destroy(kms_key_alias, prefix).init(target)
    if init:
        typer.echo(Destroy(kms_key_alias, prefix).destroy(target))
    else:
        typer.echo(init)


if __name__ == "__main__":
    cli()
