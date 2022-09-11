import boto3
import requests
from python_on_whales import docker
from functools import lru_cache


class ECRApi:
    def __init__(self) -> None:
        pass

    @lru_cache(maxsize=1)
    def api_token(self) -> str:
        return self.ecr_token_response["authorizationData"][0]["authorizationToken"]

    def get(self, url: str):
        auth = f"Basic {self.api_token()}"
        response = requests.get(
            url,
            headers={
                "Authorization": auth,
                "Accept": "application/vnd.docker.distribution.manifest.v2+json",
            },
        )
        response.raise_for_status()
        return response


class Clients:
    def __init__(self) -> None:
        self.lmb = boto3.client("lambda")
        self.iam = boto3.client("iam")
        self.sts = boto3.client("sts")
        self.ecr = boto3.client("ecr")
        self.ecr_api = ECRApi()
        self.ssm = boto3.client("ssm")
        self.cloudwatch = boto3.client("logs")
        self.docker = docker


clients = Clients()
