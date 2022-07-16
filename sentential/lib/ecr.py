import ast
import json
import os
from python_on_whales import DockerException
from requests import HTTPError
import requests
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from sentential.lib.clients import clients
from sentential.lib.spec import Spec

#
# ECR Event
# source: https://docs.aws.amazon.com/AmazonECR/latest/userguide/ecr-eventbridge.html


class ECREventDetail(BaseModel):
    result: str = "SUCCESS"
    repository_name: str = Field(alias="repository-name")
    image_digest: Optional[str] = Field(alias="image-digest")
    action_type: Optional[str] = Field(alias="action-type")
    image_tag: str = Field(alias="image-tag")


class ECREvent(BaseModel):
    version: int
    id: str
    detail_type: str = Field("ECR Image Action", const=True)
    source: str = Field("aws.ecr", const=True)
    account: str
    time: datetime = Field(datetime.now().isoformat(timespec="seconds"))
    region: str
    resources: List = []
    detail: ECREventDetail


#
# ECR Api helper
#


def retry_with_login(func):
    def wrap(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (DockerException, HTTPError) as e:
            if "404" in str(e):
                raise e  # this is hot garbage, do something better
            print("retrying after ecr login")
            clients.docker.login_ecr()
            return func(self, *args, **kwargs)

    return wrap


class ECR:
    def __init__(
        self, repository_url: str, tag: str = "latest", fetch_metadata: bool = True
    ) -> None:
        self.tag = tag
        self.repository_url = repository_url
        self.repository_name = repository_url.split("/")[-1]
        self.registry_url = repository_url.split("/")[-2]
        self.registry_api_url = f"https://{self.registry_url}/v2/{self.repository_name}"
        if fetch_metadata:
            self.ecr_token = clients.ecr.get_authorization_token()['authorizationData'][0]['authorizationToken']
            self.response = self._fetch_metadata()
            self.image_digest = self.response[0]
            self.inspect = self.response[1]

    @retry_with_login
    def push(self):
        clients.docker.image.tag(
            f"{self.repository_name}:{self.tag}", f"{self.repository_url}:{self.tag}"
        )
        clients.docker.image.push(f"{self.repository_url}:{self.tag}")

    def fetch_spec(self) -> Spec:
        data = ast.literal_eval(self._fetch_metadata()[1]["config"]["Labels"]["spec"])
        return Spec.parse_obj(data)

    def _fetch_metadata(self):
        image = clients.ecr.describe_images(
            repositoryName=self.repository_name, imageIds=[{"imageTag": self.tag}]
        )

        image_digest = image["imageDetails"][0]["imageDigest"]
        manifest = self._ecr_api_get(
            f"{self.registry_api_url}/manifests/{self.tag}"
        ).json()

        manifest_digest = manifest["config"]["digest"]
        inspect = self._ecr_api_get(
            f"{self.registry_api_url}/blobs/{manifest_digest}"
        ).json()
        return [image_digest, inspect]

    def _ecr_api_get(self, url: str):
        auth = f"Basic {self.ecr_token}"
        response = requests.get(
            url,
            headers={
                "Authorization": auth,
                "Accept": "application/vnd.docker.distribution.manifest.v2+json",
            },
        )
        response.raise_for_status()
        return response
