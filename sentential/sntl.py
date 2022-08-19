from sentential.cli.root import root
from sentential.cli.aws import aws
from sentential.cli.local import local
from sentential.cli.env import env
from sentential.cli.arg import arg

root.add_typer(local, name="local", help="work with lambda locally")
root.add_typer(aws, name="aws", help="work with lambda in aws")
root.add_typer(env, name="env", help="configure lambda runtime environment")
root.add_typer(arg, name="arg", help="configure lambda build args")


@root.command()
def wut():
    from IPython import embed
    from sentential.lib.store import Config

    embed()


def main():
    root()
