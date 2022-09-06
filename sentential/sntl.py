from sentential.cli.root import root
from sentential.cli.deploy import deploy
from sentential.cli.destroy import destroy
from sentential.cli.logs import logs
from sentential.cli.env import env
from sentential.cli.arg import arg
from sentential.cli.config import config

root.add_typer(deploy, name="deploy", help="deploy lambda")
root.add_typer(destroy, name="destroy", help="destroy lambda")
root.add_typer(logs, name="logs", help="lambda logs")
root.add_typer(env, name="env", help="configure lambda specs")
root.add_typer(arg, name="arg", help="configure lambda build args")
root.add_typer(config, name="config", help="configure lambda environment")

def main():
    root()
