from sentential.cli.root import root
from sentential.cli.aws import aws
from sentential.cli.local import local
from sentential.cli.config import config
from sentential.cli.secret import secret

root.add_typer(local, name="local", help="ops for {repository}")
root.add_typer(aws, name="aws", help="ops for {repository}")
root.add_typer(secret, name="secret", help="for {repository}")
root.add_typer(config, name="config", help="for {repository}")


def main():
    root()
