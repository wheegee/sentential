from python_on_whales import DockerException
from sentential.lib.clients import clients
from pydantic import ValidationError

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
    try:
        root()
    # TODO: start handling terminating exceptions here, tart it up later
    except clients.ecr.exceptions.RepositoryNotFoundException as e:
        print(e.response["message"])
        exit(1)
    except DockerException as e:
        print(f"failed: {e.docker_command}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        exit(1)
    except ValidationError as e:
        print(e)
        exit(1)
