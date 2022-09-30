from sentential.cli.root import root
from sentential.cli.args import args
from sentential.cli.envs import envs
from sentential.cli.configs import configs

root.add_typer(args, name="args", help="build arguments")
root.add_typer(envs, name="envs", help="environment variables")
root.add_typer(configs, name="configs", help="provisioning")


def main():
    root()
