from typing import Union
from sentential.lib.context import Context
from sentential.lib.store import GenericStore, ModeledStore


class Ontology:
    def __init__(self) -> None:
        pass

    @property
    def context(cls) -> Context:
        return Context()

    @property
    def args(cls) -> Union[GenericStore, ModeledStore]:
        try:
            from shapes import Args as Model  # type: ignore

            return ModeledStore(cls.context, "arg", Model)
        except:
            return GenericStore(cls.context, "arg")

    @property
    def envs(cls) -> Union[GenericStore, ModeledStore]:
        try:
            from shapes import Envs as Model  # type: ignore

            return ModeledStore(cls.context, "env", Model)
        except:
            return GenericStore(cls.context, "env")

    @property
    def configs(cls) -> ModeledStore:
        from sentential.lib.shapes import Provision as Model

        return ModeledStore(cls.context, "provision", Model)
