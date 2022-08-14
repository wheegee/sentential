from sentential.cli.root import root
from sentential.cli.aws import aws
from sentential.cli.local import local
from sentential.cli.env import env

root.add_typer(local, name="local", help="ops for {repository}")
root.add_typer(aws, name="aws", help="ops for {repository}")
root.add_typer(env, name="env", help="for {repository}")


def main():
    root()
