import re
from typing import List
import semantic_version as semver
from distutils.version import LooseVersion

from sentential.lib.shapes import Image

# pyright: reportInvalidStringEscapeSequence=false
SEMVER_REGEX = "^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"


class SemVer:
    def __init__(self, images: List[Image]) -> None:
        self.images = images

    @property
    def versions(self) -> List[str]:
        images = self.images
        versions = []
        for image in images:
            for version in image.versions:
                versions.append(version)
        return list(set(versions))

    @property
    def semver(self) -> List[str]:
        matcher = re.compile(SEMVER_REGEX)
        versions = self.versions
        versions = [version for version in versions if matcher.match(version)]
        versions = sorted(versions, key=lambda v: LooseVersion(v))
        return versions

    @property
    def latest(self) -> str:
        if self.semver:
            return self.semver[-1]
        else:
            return "0.0.0"

    def next(self, major=False, minor=False) -> str:
        latest = semver.Version(self.latest)
        if major:
            return str(latest.next_major())
        if minor:
            return str(latest.next_minor())
        else:
            return str(latest.next_patch())
