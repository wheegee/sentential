import ast
import json
import requests
from sentential.lib.clients import clients
from sentential.lib.shapes.aws import ECREvent
from sentential.lib.shapes.internal import Spec

#
# ECR
#

class ECR:
    def __init__(self, event: ECREvent) -> None:
        self.event = event
        self.repository_name = event.detail.repository_name
        self.registry_url = f"{event.account}.dkr.ecr.{event.region}.amazonaws.com"
        self.repository_url = f"{self.registry_url}/{event.detail.repository_name}"
        self.registry_api_url = f"https://{self.registry_url}/v2/{self.repository_name}"

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

#
# ECR Image
#

class Image(ECR):
    def __init__(self, event: ECREvent) -> None:
        super().__init__(event)
        self.name = self.repository_name
        self.tag = event.detail.image_tag
        self.uri = f"{self.repository_url}:{self.tag}"
        self.ecr_token_response = clients.ecr.get_authorization_token()
        self.ecr_token = self.ecr_token_response["authorizationData"][0]["authorizationToken"]
        self.metadata_v1 = self._fetch_image_metadata("application/vnd.docker.distribution.manifest.v1+json")
        self.metadata_v2 = self._fetch_image_metadata("application/vnd.docker.distribution.manifest.v2+json")
        self.digest = self.metadata_v2['imageId']['imageDigest']
        self.manifest_v1 = self._parse_image_manifest(self.metadata_v1)
        self.manifest_v2 = self._parse_image_manifest(self.metadata_v2)
        self.manifest_digest = self.manifest_v2['config']['digest']
        self.inspect = self._fetch_image_inspect()
        self.spec = self._parse_image_spec()
        self.architecture = self._parse_architecture()

    def _fetch_image_metadata(self, media_type: str) -> dict:
        return clients.ecr.batch_get_image(
                repositoryName=self.name, 
                imageIds=[{"imageTag": self.tag}], 
                acceptedMediaTypes=[media_type]
            )['images'][0]

    def _parse_image_manifest(self, metadata: dict) -> dict:
        return json.loads(metadata['imageManifest'])

    def _fetch_image_inspect(self) -> dict:
        return self._ecr_api_get(
            f"{self.registry_api_url}/blobs/{self.manifest_digest}"
        ).json()

    def _parse_image_spec(self) -> Spec:
        data = ast.literal_eval(self.inspect["config"]["Labels"]["spec"])
        return Spec.parse_obj(data)

    def _parse_architecture(self) -> str:
        if self.manifest_v1["architecture"] == "amd64":
            return "x86_64"
        else:
            return "arm64"






