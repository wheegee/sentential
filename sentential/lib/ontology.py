import os
import sys
import importlib
from typing import Union
from sentential.lib.context import Context
from sentential.lib.store import GenericStore, ModeledStore
from sentential.lib.shapes import Provision as Model


def reload_shapes():
    if os.getcwd() not in sys.path:
        sys.path.append(os.getcwd())
    import shapes

    importlib.reload(shapes)


class Ontology:
    def __init__(self) -> None:
        pass

    @property
    def context(cls) -> Context:
        return Context()

    @property
    def args(cls) -> Union[GenericStore, ModeledStore]:
        try:
            reload_shapes()
            from shapes import Args as Model  # type: ignore

            return ModeledStore(cls.context, "arg", Model)
        except:
            return GenericStore(cls.context, "arg")

    @property
    def envs(cls) -> Union[GenericStore, ModeledStore]:
        try:
            reload_shapes()
            from shapes import Envs as Model  # type: ignore

            return ModeledStore(cls.context, "env", Model)
        except:
            return GenericStore(cls.context, "env")

    @property
    def configs(cls) -> ModeledStore:
        return ModeledStore(cls.context, "provision", Model)
