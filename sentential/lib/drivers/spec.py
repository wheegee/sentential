from abc import ABC, abstractclassmethod, abstractmethod

from sentential.lib.shapes import Function


class LambdaDriver(ABC):
    @abstractmethod
    def deployed(cls):
        ...

    @abstractmethod
    def images(self):
        ...

    @abstractmethod
    def image(self, version: str):
        ...

    @abstractmethod
    def deploy(self):
        ...

    @abstractmethod
    def destroy(self):
        ...

    @abstractmethod
    def logs(self, follow: bool):
        ...

    @abstractmethod
    def invoke(self, payload: str):
        ...


class MountDriver(ABC):
    @abstractclassmethod
    def autocomplete(cls):
        ...

    def mount(self, path):
        ...

    def umount(self, path):
        ...

    def mounts(self):
        ...
