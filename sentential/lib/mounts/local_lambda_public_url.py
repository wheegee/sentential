from typing import List
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology

class LocalLambdaPublicUrlMount:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology

    def mount(self) -> str:
        return self._put_url()

    def umount(self) -> None:
        return self._delete_url()

    def mounts(self) -> List[str]:
        if [c for c in clients.docker.ps() if c.name == "sentential-gw"]:
            return ["http://localhost:8081"]
        else:
            return []

    def _put_url(self) -> str:
        clients.docker.run(
            "ghcr.io/wheegee/sentential-gw:latest",
            name="sentential-gw",
            hostname="sentential-gw",
            networks=["sentential-bridge"],
            detach=True,
            remove=False,
            publish=[("8081", "8081")],
            envs={"LAMBDA_ENDPOINT": "http://sentential:8080"},
        )
        return "http://localhost:8081"

    def _delete_url(self) -> None:
        clients.docker.remove(["sentential-gw"], force=True, volumes=True)
        return None