from typing import List
from sentential.lib.clients import clients
from sentential.lib.drivers.local_bridge import LocalBridge
from sentential.lib.ontology import Ontology


class LocalLambdaPublicUrlMount:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology

    def mount(self) -> str:
        return self._put_url()

    def umount(self) -> None:
        return self._delete_url()

    def mounts(self) -> List[str]:
        if [c for c in clients.docker.ps() if c.name == LocalBridge.config.gw_name]:
            return [LocalBridge.config.gw_port]
        else:
            return []

    def _put_url(self) -> str:
        if not self._running():
            clients.docker.run(
                LocalBridge.config.gw_image,
                name=LocalBridge.config.gw_name,
                hostname=LocalBridge.config.gw_name,
                networks=[LocalBridge.config.bridge_name],
                detach=True,
                remove=False,
                publish=[
                    (LocalBridge.config.gw_port, LocalBridge.config.gw_internal_port)
                ],
                envs={
                    "LAMBDA_ENDPOINT": f"http://{LocalBridge.config.lambda_name}:{LocalBridge.config.lambda_internal_port}"
                },
            )
        return f"http://localhost:{LocalBridge.config.gw_port}"

    def _delete_url(self) -> None:
        clients.docker.remove([LocalBridge.config.gw_name], force=True, volumes=True)
        return None

    def _running(self) -> bool:
        found = [
            container.name == LocalBridge.config.gw_name
            for container in clients.docker.container.list()
        ]
        return any(found)
