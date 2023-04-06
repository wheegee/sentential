import os
import sys
from sentential.lib.context import Context
from sentential.lib.store_v2 import StoreV2


def load_user_defined_shapes():
    if os.getcwd() not in sys.path:
        sys.path.append(os.getcwd())

    if "shapes" in sys.modules:
        del sys.modules["shapes"]

    import shapes


class Ontology:
    def __init__(self) -> None:
        pass

    @property
    def context(self) -> Context:
        return Context()

    @property
    def args(self) -> StoreV2:
        try:
            load_user_defined_shapes()
            from shapes import Args
        except ImportError:
            from sentential.lib.shapes import Args
        return StoreV2(self.context, Args)

    @property
    def envs(self) -> StoreV2:
        try:
            load_user_defined_shapes()
            from shapes import Envs
        except ImportError:
            from sentential.lib.shapes import Envs
        return StoreV2(self.context, Envs)

    @property
    def secrets(self) -> StoreV2:
        try:
            load_user_defined_shapes()
            from shapes import Secrets
        except ImportError:
            from sentential.lib.shapes import Secrets
        return StoreV2(self.context, Secrets)

    @property
    def tags(self) -> StoreV2:
        try:
            load_user_defined_shapes()
            from shapes import Tags
        except ImportError:
            from sentential.lib.shapes import Tags
        return StoreV2(self.context, Tags)

    @property
    def configs(self) -> StoreV2:
        from sentential.lib.shapes import Provision

        return StoreV2(self.context, Provision)
