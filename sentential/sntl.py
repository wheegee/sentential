from sentential.cli.root import root
from sentential.cli.store import store
from sentential.cli.deploy import deploy
from sentential.cli.destroy import destroy
from sentential.cli.mount import mount
from sentential.cli.umount import umount
from sentential.cli.invoke import invoke
from sentential.cli.logs import logs
from sentential.cli.policy import policy
from sentential.lib.assurances import Assurances

from sentential.lib.exceptions import (
    SntlException,
    DockerException,
    AWS_EXCEPTIONS,
    ValidationError,
)

root.add_typer(store, name="args", help="build arguments", callback=Assurances.build)
root.add_typer(store, name="envs", help="environment variables")
root.add_typer(store, name="secrets", help="secrets")
root.add_typer(store, name="configs", help="provisioning")
root.add_typer(store, name="tags", help="tagging")
root.add_typer(
    deploy, name="deploy", help="create deployment", callback=Assurances.deploy
)
root.add_typer(destroy, name="destroy", help="destroy deployment")
root.add_typer(mount, name="mount", help="mount integration")
root.add_typer(umount, name="umount", help="unmount integration")
root.add_typer(invoke, name="invoke", help="invoke function")
root.add_typer(logs, name="logs", help="logging")
root.add_typer(
    policy,
    name="policy",
    help="inspect and render policy.json",
    callback=Assurances.render,
)


def main():
    try:
        root()
    except (SntlException, ValidationError) as e:
        print(f"SENTENTIAL: {e}")
        exit(1)
    except AWS_EXCEPTIONS as e:
        print(f"AWS: {e}")
        exit(1)
    except DockerException as e:
        print(f"DOCKER: {e}")
        exit(e.return_code)
