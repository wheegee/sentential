from sentential.cli.root import root
from sentential.cli.aws import aws
from sentential.cli.local import local
from sentential.cli.env import env
from sentential.cli.arg import arg
from sentential.cli.config import config

root.add_typer(local, name="local", help="work with lambda locally")
root.add_typer(aws, name="aws", help="work with lambda in aws")
root.add_typer(env, name="env", help="configure lambda runtime environment")
root.add_typer(arg, name="arg", help="configure lambda build args")
root.add_typer(config, name="config", help="configure lambda provisioning")


def main():
    root()
