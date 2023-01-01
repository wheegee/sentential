from abc import ABC, abstractmethod


class LambdaDriver(ABC):
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

class ImagesDriver(ABC):
    @abstractmethod
    def images(self):
        ...
    
    @abstractmethod
    def clean(self):
        ...

    @abstractmethod
    def image_by_tag(self):
        ...

    @abstractmethod
    def image_by_digest(self):
        ...
    
    @abstractmethod
    def image_by_id(self):
        ...