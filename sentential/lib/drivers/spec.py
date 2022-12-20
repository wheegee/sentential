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
