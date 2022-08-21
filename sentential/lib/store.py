from functools import lru_cache
from typing import Union
from sentential.lib.clients import clients
from types import SimpleNamespace
from sentential.lib.facts import Factual
from rich.table import Table
from rich import print
import sys
import os
import polars as pl
from pydantic import ValidationError


sys.path.append(os.getcwd())


class Store(Factual):
    def __init__(self, suffix: str, model: object = None):
        super().__init__()
        self.model = model
        self.path = f"/{self.facts.partition}/{self.facts.repository_name}/{suffix}/"
        self.chamber_path = (
            f"{self.facts.partition}/{self.facts.repository_name}/{suffix}"
        )
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

    # TODO: rename to as_simple_namespace
    def parameters(self):
        if self.model is not None:
            return self.model(**self.as_dict())
        else:
            return SimpleNamespace(**self.as_dict())

    def data(self):
        data = self.as_dict()
        data = [list(data.keys()), list(data.values())]
        return pl.DataFrame(data, columns=[("field", pl.Utf8), ("persisted", pl.Utf8)])

    def validation(self):
        columns = [("field", pl.Utf8), ("validation", pl.Utf8)]
        try:
            self.model(**self.as_dict())
            return pl.DataFrame([[], []], columns=columns)
        except ValidationError as e:
            return pl.DataFrame(
                [
                    ["/".join(list(e["loc"])) for e in e.errors()],
                    [e["msg"] for e in e.errors()],
                ],
                columns=columns,
            )

    def schema(self):
        fields = list(self.model.schema()["properties"].keys())
        properties = list(self.model.schema()["properties"].values())
        columns = [("field", pl.Utf8), ("default", pl.Utf8), ("description", pl.Utf8)]
        return pl.DataFrame(
            [
                fields,
                [str(p["default"]) if "default" in p else None for p in properties],
                [p["description"] if "description" in p else None for p in properties],
            ],
            columns=columns,
        )

    def read(self):
        data = self.data()
        if self.model is not None:
            opts = {"on": "field", "how": "outer"}
            schema = self.schema()
            validation = self.validation()
            df = schema.join(data, **opts).join(validation, **opts)
            df = df.with_columns(
                [(pl.col("persisted").fill_null(pl.col("default"))).alias("value")]
            )
            from IPython import embed

            # embed()
            print(
                df.select(
                    [
                        pl.col("field"),
                        pl.col("value"),
                        pl.col("validation"),
                        pl.col("description"),
                    ]
                )
            )
        else:
            print(data.select([pl.col("field"), pl.col("persisted").alias("value")]))

    def write(self, key: str, value: str):
        kwargs = {
            "Name": f"{self.path}{key}",
            "Value": value,
            "Type": "SecureString",
            "Overwrite": True,
            "Tier": "Standard",
            "KeyId": self.kms_key_id,
        }
        if self.model is not None:
            try:
                field = self.model.__fields__[key]
                err = field.validate(value, [], loc=key)[1]
                if err is not None:
                    raise ValueError(err.exc.msg_template)
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


class Env(Store):
    def __init__(self):
        try:
            from shapes import Env as Model

            super().__init__("env", Model)
        except ImportError:
            super().__init__("env")


class Arg(Store):
    def __init__(self):
        try:
            from shapes import Arg as Model

            super().__init__("arg", Model)
        except ImportError:
            super().__init__("arg")


class Provision(Store):
    def __init__(self):
        try:
            from shapes import Provision as Model

            super().__init__("config", Model)
        except ImportError:
            super().__init__("config")
