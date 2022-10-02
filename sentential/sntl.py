from sentential.cli.root import root
from sentential.cli.args import args
from sentential.cli.envs import envs
from sentential.cli.configs import configs
from sentential.cli.deploy import deploy
from sentential.cli.destroy import destroy
from sentential.cli.logs import logs
from sentential.cli.images import images
from sentential.cli.deployments import deployments

root.add_typer(args, name="args", help="build arguments")
root.add_typer(envs, name="envs", help="environment variables")
root.add_typer(configs, name="configs", help="provisioning")
root.add_typer(deploy, name="deploy", help="create deployment")
root.add_typer(destroy, name="destroy", help="destroy deployment")
root.add_typer(logs, name="logs", help="logging")
root.add_typer(images, name="images", help="list images")
root.add_typer(deployments, name="deployments", help="list deployments")

def main():
    root()
