from abc import ABC, abstractclassmethod, abstractmethod


class MountDriver(ABC):
    @abstractclassmethod
    def autocomplete(cls):
        ...

    def mount(self):
        ...

    def umount(self):
        ...

    def mounts(self):
        ...
