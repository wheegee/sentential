from sentential.cli.root import root
from sentential.cli.aws import aws
from sentential.cli.local import local
from sentential.cli.config import config
from sentential.cli.secret import secret
from sentential.lib.facts import require_sntl_file

root.add_typer(local, name="local", help="ops for {repository}", callback=require_sntl_file)
root.add_typer(aws, name="aws", help="ops for {repository}", callback=require_sntl_file)
root.add_typer(secret, name="secret", help="for {repository}", callback=require_sntl_file)
root.add_typer(config, name="config", help="for {repository}", callback=require_sntl_file)


def main():
    root()
