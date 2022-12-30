import polars as pl
from typing import List, Type
from types import SimpleNamespace
from pydantic import ValidationError
from rich.table import Table, box
from builtins import ValueError
from sentential.lib.exceptions import StoreError
from sentential.lib.clients import clients
from sentential.lib.context import Context
from sentential.support.shaper import Shaper, ShaperError


class Common:
    path: str
    context: Context

    def _fetch(self):
        return clients.ssm.get_parameters_by_path(
            Path=self.path,
            Recursive=True,
            WithDecryption=True,
        )["Parameters"]

    def _unsafe_dict(self):
        return {p["Name"].replace(self.path, ""): p["Value"] for p in self._fetch()}

    def _unsafe_df(self):
        data = self._unsafe_dict()
        data = [list(data.keys()), list(data.values())]
        return pl.DataFrame(data, columns=[("field", pl.Utf8), ("value", pl.Utf8)])

    def delete(self, key: str):
        try:
            return clients.ssm.delete_parameter(Name=f"{self.path}{key}")
        except clients.ssm.exceptions.ParameterNotFound:
            raise StoreError(f"no key '{key}' persisted")

    def clear(self):
        for (key, value) in self._unsafe_dict().items():
            self.delete(key)


class GenericStore(Common):
    def __init__(self, context: Context, prefix: str) -> None:
        super().__init__()
        self.context = context
        self.path = (
            f"/{self.context.partition}/{self.context.repository_name}/{prefix}/"
        )

    @property
    def parameters(self) -> SimpleNamespace:
        return SimpleNamespace(**self._unsafe_dict())

    def as_dict(self):
        return vars(self.parameters)

    def read(self) -> Table:
        data = self._unsafe_dict()
        table = Table("field", "value", box=box.SIMPLE)
        for (key, value) in data.items():
            table.add_row(key, value)
        return table

    def write(self, key: str, value: List[str]):
        # Typer doesn't support Union[str, List[str]], understandably
        # So desired behavior is implemented here, to the insult of typing

        delimiter = ","
        value = delimiter.join(value)  # type: ignore

        return clients.ssm.put_parameter(
            Name=f"{self.path}{key}",
            Value=str(value),
            Type="SecureString",
            Overwrite=True,
            Tier="Standard",
            KeyId=self.context.kms_key_id,
        )

    def export_defaults(self) -> None:
        return None


class ModeledStore(Common):
    def __init__(self, context: Context, prefix: str, model: Type[Shaper]) -> None:
        super().__init__()
        self.context = context
        self.model = model
        self.path = (
            f"/{self.context.partition}/{self.context.repository_name}/{prefix}/"
        )

    def export_defaults(self) -> None:
        if self.model:
            current_state = self._unsafe_dict()
            for (name, field) in self.model.__fields__.items():
                if field.name not in current_state.keys():
                    if hasattr(field, "default") and field.default != None:
                        self.write(field.name, field.default)

    @property
    def parameters(self) -> Shaper:
        try:
            return self.model.constrained_parse_obj(self._unsafe_dict())
        except ValidationError as e:
            raise StoreError(e)

    def as_dict(self) -> dict:
        return self.parameters.dict()

    def read(self) -> Table:
        data = self._unsafe_df()
        opts = {"on": "field", "how": "outer"}
        schema = self.model.schema_df()
        validation = self.model.constrained_validation_df(self._unsafe_dict())
        df = schema.join(data, **opts).join(validation, **opts)
        df = df.with_columns([(pl.col("value").fill_null(pl.col("default")))])
        df = df.select(
            [
                pl.col("field"),
                pl.col("value"),
                pl.col("validation"),
                pl.col("description"),
            ]
        )

        table = Table(*df.columns, box=box.SIMPLE)
        for row in df.rows():
            table.add_row(*[str(value) for value in row])
        return table

    def write(self, key: str, value: List[str]):

        # Typer doesn't support Union[str, List[str]], understandably
        # So desired behavior is implemented here, to the insult of typing
        if len(value) == 1:
            value = value[0]  # type: ignore

        try:
            self.model.validate_field_value(key, value)
        except ValueError as e:
            raise StoreError(e)
        except ShaperError as e:
            raise StoreError(e)

        return clients.ssm.put_parameter(
            Name=f"{self.path}{key}",
            Value=str(value),
            Type="SecureString",
            Overwrite=True,
            Tier="Standard",
            KeyId=self.context.kms_key_id,
        )
