import ast
import requests
from requests import HTTPError
from python_on_whales import DockerException
from sentential.lib.clients import clients
from sentential.lib.shapes.internal import Spec


#
# ECR Rest API helper
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
            self.ecr_token = clients.ecr.get_authorization_token()["authorizationData"][
                0
            ]["authorizationToken"]
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
