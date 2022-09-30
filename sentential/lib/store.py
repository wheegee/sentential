import polars as pl
from typing import List, Type
from types import SimpleNamespace
from rich.table import Table
from builtins import KeyError, ValueError
from sentential.lib.clients import clients
from sentential.lib.context import Context
from sentential.support.shaper import Shaper

class StoreError(BaseException):
    pass

class Common():
    path: str
    context: Context

    def _fetch(self):
        return clients.ssm.get_parameters_by_path(
            Path=self.path,
            Recursive=True,
            WithDecryption=True,
        )["Parameters"]

    def as_dict(self):
        return {p["Name"].replace(self.path, ""): p["Value"] for p in self._fetch()}

    def as_df(self):
        data = self.as_dict()
        data = [list(data.keys()), list(data.values())]
        return pl.DataFrame(data, columns=[("field", pl.Utf8), ("value", pl.Utf8)])

    def delete(self, key: str):
        try:
            return clients.ssm.delete_parameter(Name=f"{self.path}{key}")
        except clients.ssm.exceptions.ParameterNotFound:
            raise StoreError(f"no such key '{key}'")

    def clear(self):
        for (key, value) in self.as_dict().items():
            self.delete(key)

class GenericStore(Common):
    def __init__(self, context: Context, prefix: str) -> None:
        super().__init__()
        self.context = context
        self.path = f"/{self.context.partition}/{self.context.repository_name}/{prefix}/"

    def parameters(self) -> SimpleNamespace:
        return SimpleNamespace(**self.as_dict())

    def read(self) -> Table:
        data = self.as_dict()
        table = Table("field", "value")
        for (key, value) in data.items():
            table.add_row(key, value)
        return table

    def write(self, key: str, value: List[str]):
        return clients.ssm.put_parameter(
            Name=f"{self.path}{key}",
            Value=str(value),
            Type="SecureString",
            Overwrite=True,
            Tier="Standard",
            KeyId=self.context.kms_key_id,
        )


class ModeledStore(Common):
    def __init__(self, context: Context, prefix: str, model: Type[Shaper]) -> None:
        super().__init__()
        self.context = context
        self.model = model
        self.path = f"/{self.context.partition}/{self.context.repository_name}/{prefix}/"

    def _export_defaults(self) -> None:
        if self.model:
            current_state = self.as_dict()
            for (name, field) in self.model.__fields__.items():
                if field.name not in current_state.keys():
                    if hasattr(field, "default") and field.default != None:
                        self.write(field.name, field.default)
        self._fetch.cache_clear()

    def parameters(self) -> Shaper:
        self._export_defaults()
        return self.model.constrained_parse_obj(self.as_dict())

    def read(self) -> Table:
        data = self.as_df()
        opts = {"on": "field", "how": "outer"}
        schema = self.model.schema_df()
        validation = self.model.constrained_validation_df(self.as_dict())
        df = schema.join(data, **opts).join(validation, **opts)
        df = df.with_columns(
            [(pl.col("value").fill_null(pl.col("default")))]
        )
        df = df.select(
            [
                pl.col("field"),
                pl.col("value"),
                pl.col("validation"),
                pl.col("description"),
            ]
        )

        table = Table(*df.columns)
        for row in df.rows():
            table.add_row(*[str(value) for value in row])
        return table

    def write(self, key: str, value: List[str]):
        try:
            validation = self.model.constrained_validation_df({key: value})
            validation = validation.filter(pl.col("field") == key)
            if validation.row(0)[1] is not None:
                raise ValueError(validation.row(0)[1])
        except KeyError:
            raise StoreError(f"invalid key, valid options {list(self.model.__fields__.keys())}")
        except ValueError as e:
            raise StoreError(e)

        return clients.ssm.put_parameter(
            Name=f"{self.path}{key}",
            Value=str(value),
            Type="SecureString",
            Overwrite=True,
            Tier="Standard",
            KeyId=self.context.kms_key_id,
        )
