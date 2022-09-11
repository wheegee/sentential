from builtins import KeyError, ValueError
from functools import lru_cache
from typing import List
from sentential.lib.clients import clients
from types import SimpleNamespace
from sentential.lib.facts import Factual
import sys
import os
import polars as pl
from rich.table import Table
from rich import print
import importlib


class Store(Factual):
    def __init__(self, suffix: str, model: object = None):
        super().__init__()
        self.model = model
        self.path = f"/{self.facts.partition}/{self.facts.repository_name}/{suffix}/"
        self.kms_key_id = self.facts.kms_key_id

    @lru_cache()
    def fetch(self):
        return clients.ssm.get_parameters_by_path(
            Path=self.path,
            Recursive=True,
            WithDecryption=True,
        )["Parameters"]

    def as_dict(self):
        return {p["Name"].replace(self.path, ""): p["Value"] for p in self.fetch()}

    def parameters(self):
        if self.model is not None:
            return self.model.constrained_parse_obj(self.as_dict())
        else:
            return SimpleNamespace(**self.as_dict())

    def ssm_df(self):
        data = self.as_dict()
        data = [list(data.keys()), list(data.values())]
        return pl.DataFrame(data, columns=[("field", pl.Utf8), ("persisted", pl.Utf8)])

    def state_df(self):
        data = self.ssm_df()
        if self.model is not None:
            opts = {"on": "field", "how": "outer"}
            schema = self.model.schema_df()
            validation = self.model.constrained_validation_df(self.as_dict())
            df = schema.join(data, **opts).join(validation, **opts)
            df = df.with_columns(
                [(pl.col("persisted").fill_null(pl.col("default"))).alias("value")]
            )
            return df.select(
                [
                    pl.col("field"),
                    pl.col("value"),
                    pl.col("validation"),
                    pl.col("description"),
                ]
            )
        else:
            return data.select([pl.col("field"), pl.col("persisted").alias("value")])

    def read(self):
        data = self.state_df()
        table = Table(*data.columns)
        for row in data.rows():
            table.add_row(*[str(value) for value in row])
        print(table)

    def write(self, key: str, value: List[str]):
        kwargs = {
            "Name": f"{self.path}{key}",
            "Value": str(value),
            "Type": "SecureString",
            "Overwrite": True,
            "Tier": "Standard",
            "KeyId": self.kms_key_id,
        }
        if self.model is not None:
            try:
                validation = self.model.constrained_validation_df({key: value})
                validation = validation.filter(pl.col("field") == key)
                if validation.row(0)[1] is not None:
                    raise ValueError(validation.row(0)[1])
            except KeyError:
                print(
                    f"invalid key, valid options {list(self.model.__fields__.keys())}"
                )
                exit(1)
            except ValueError as e:
                print(e)
                exit(1)

        return clients.ssm.put_parameter(**kwargs)

    def delete(self, key: str):
        try:
            return clients.ssm.delete_parameter(Name=f"{self.path}{key}")
        except clients.ssm.exceptions.ParameterNotFound:
            pass

    def export_defaults(self):
        if self.model:
            current_state = self.as_dict()
            for (name, field) in self.model.__fields__.items():
                if field.name not in current_state.keys():
                    if hasattr(field, "default") and field.default != None:
                        self.write(field.name, field.default)
        self.fetch.cache_clear()

    def clear(self):
        for (key, value) in self.as_dict().items():
            # TODO: do this with a bulk op
            self.delete(key)


def reload_shapes():
    # This method is used to ensure cached objects in testing don't hold stale import information about shapes.py
    if os.getcwd() not in sys.path:
        sys.path.append(os.getcwd())
    import shapes

    importlib.reload(shapes)


class Env(Store):
    def __init__(self):
        try:
            reload_shapes()
            from shapes import Env as Model

            super().__init__("env", Model)
        except ImportError:
            super().__init__("env")


class Arg(Store):
    def __init__(self):
        try:
            reload_shapes()
            from shapes import Arg as Model

            super().__init__("arg", Model)
        except ImportError:
            super().__init__("arg")


class Tag(Store):
    def __init__(self):
        try:
            reload_shapes()
            from shapes import Tag as Model

            super().__init__("tag", Model)
        except ImportError:
            super().__init__("tag")


class Provision(Store):
    def __init__(self):
        try:
            from sentential.lib.shapes.internal import Provision as Model

            super().__init__("config", Model)
        except ImportError:
            super().__init__("config")
