from typing import List
from sentential.lib.drivers.spec import Driver
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Image
from sentential.lib.clients import clients


class AwsDriver(Driver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology

    def deployed(cls):
        ...

    def images(self):
        repo = self.ontology.context.repository_name
        images = clients.ecr.describe_images(repositoryName=repo)
        images = [ { 'imageDigest': image['imageDigest'] } for image in images ]
        # then batch_get_image
        # then get image id / arch
        from IPython import embed
        embed()

    def image(self, version: str):
        ...

    def deploy(self):
        ...

    def destroy(self):
        ...

    def logs(self, follow: bool):
        ...

    def invoke(self, payload: str):
        ...




# class Repository(Factual):
#     def __init__(self) -> None:
#         super().__init__()
#         pass

#     def images(self) -> List[Image]:
#         images = clients.ecr.describe_images(repositoryName=self.facts.repository_name)[
#             "imageDetails"
#         ]
#         filtered = []
#         for image in images:
#             if "imageTags" in image:
#                 for tag in image["imageTags"]:
#                     # TODO: performance => let image be prepopulated with metadata at init, do bulk request here
#                     filtered.append(Image(tag))
#         return filtered

#     def semver(self) -> List[Image]:
#         matcher = re.compile(SEMVER_REGEX)
#         images = [image for image in self.images() if matcher.match(image.tag)]
#         images.sort(key=lambda image: LooseVersion(image.tag))
#         return images

#     def latest(self) -> Image:
#         try:
#             return self.semver()[-1]
#         except IndexError:
#             return None
