import os
import sys
from typing import List
from sentential.lib.context import Context
from sentential.lib.store import Store


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
    def args(self) -> Store:
        try:
            load_user_defined_shapes()
            from shapes import Args
        except ImportError:
            from sentential.lib.shapes import Args
        return Store(self.context, Args)

    @property
    def envs(self) -> Store:
        try:
            load_user_defined_shapes()
            from shapes import Envs
        except ImportError:
            from sentential.lib.shapes import Envs
        return Store(self.context, Envs)

    @property
    def secrets(self) -> Store:
        try:
            load_user_defined_shapes()
            from shapes import Secrets
        except ImportError:
            from sentential.lib.shapes import Secrets
        return Store(self.context, Secrets)

    @property
    def tags(self) -> Store:
        try:
            load_user_defined_shapes()
            from shapes import Tags
        except ImportError:
            from sentential.lib.shapes import Tags
        return Store(self.context, Tags)

    @property
    def configs(self) -> Store:
        from sentential.lib.shapes import Configs

        return Store(self.context, Configs)

    def export_store_defaults(self) -> List[Store]:
        stores = [self.args, self.envs, self.secrets, self.tags, self.configs]
        for store in stores:
            store.export_defaults()
        return stores

    def clear_stores(self) -> List[Store]:
        stores = [self.args, self.envs, self.secrets, self.tags, self.configs]
        for store in stores:
            store.clear()
        return stores
