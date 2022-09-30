from functools import lru_cache
import boto3
import requests
from python_on_whales import docker

class ECRApi:
    def __init__(self) -> None:
        self.ecr = boto3.client("ecr")

    @lru_cache(maxsize=1)
    def api_token(self) -> str:
        response = self.ecr.get_authorization_token()
        return response["authorizationData"][0]["authorizationToken"]

    def v1(self):
        return {
            "Authorization": f"Basic {self.api_token()}",
            "Accept": "application/vnd.docker.distribution.manifest.v1+json",  
        }
        

    def v2(self):
        return {
            "Authorization": f"Basic {self.api_token()}",
            "Accept": "application/vnd.docker.distribution.manifest.v2+json",  
        }


    def get(self, url: str):
        response = requests.get(
            url,
            headers=self.v1()
        )
        response.raise_for_status()
        return response

    def head(self, url: str):
        response = requests.head(
            url,
            headers=self.v1()
        )
        response.raise_for_status()
        return response

class Clients:
    def __init__(self) -> None:
        self.lmb = boto3.client("lambda")
        self.iam = boto3.client("iam")
        self.sts = boto3.client("sts")
        self.ecr = boto3.client("ecr")
        self.ssm = boto3.client("ssm")
        self.ecr_api = ECRApi()
        self.cloudwatch = boto3.client("logs")
        self.docker = docker


clients = Clients()
