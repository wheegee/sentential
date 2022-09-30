from unittest.mock import sentinel
from typing import List
from sentential.lib.drivers.spec import Driver
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Image
from sentential.lib.clients import clients

class Aws(Driver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology

    def images(self) -> List[Image]:
        clients.ecr
    
    def image(self, version: str):
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