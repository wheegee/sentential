from types import SimpleNamespace
from sentential.lib.clients import clients
from typing import Dict


class LocalBridge:
    config: SimpleNamespace = SimpleNamespace(
        **{
            "bridge_name": "sentential-bridge",
            "gw_image": "ghcr.io/wheegee/sentential-gw:latest",
            "gw_name": "sentential-gw",
            "gw_internal_port": "8081",
            "gw_port": "8999",
            "lambda_name": "sentential",
            "lambda_internal_port": "8080",
            "lambda_port": "9000",
        }
    )

    @classmethod
    def setup(cls):
        networks = clients.docker.network.list()
        if not any([network.name == cls.config.bridge_name for network in networks]):
            clients.docker.network.create(cls.config.bridge_name)

    @classmethod
    def teardown(cls):
        clients.docker.network.remove(cls.config.bridge_name)
