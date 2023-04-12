import json
from pathlib import PosixPath
from rich.table import Table, box
from typing import Any, Dict, List, Optional, Tuple, cast, Type, Union
from pydantic import BaseModel, Json, ValidationError
from sentential.lib.clients import clients
from sentential.lib.context import Context
from sentential.lib.shapes import AwsSSMParam, Args, Envs, Secrets, Tags, Configs

VALID_MODEL_TYPES = Union[
    Type[Args], Type[Envs], Type[Secrets], Type[Tags], Type[Configs]
]
VALID_MODELS = Union[Args, Envs, Secrets, Tags, Configs]


class ValidationErrorInfo(BaseModel):
    key: str
    loc: Tuple
    msg: str
    type: str


class StoreTableRow(BaseModel):
    key: Any
    value: Optional[Any]
    description: Optional[Any]
    validation: Optional[Any]


class Store:
    # TODO: the fact that this must take Context instead of Ontology, is because this belongs in an Epistemology.
    # The conflation of the two logically leads to a circular import. A part of our Epistemology is our Ontology (prior knowledge).
    def __init__(self, context: Context, model: VALID_MODEL_TYPES) -> None:
        self.kms_key_id = context.kms_key_id
        self.partition: str = context.partition
        self.repo: str = context.repository_name
        self.root: PosixPath = PosixPath(f"/{self.partition}/{self.repo}")
        self.model: VALID_MODEL_TYPES = model
        self.path: PosixPath = self.root.joinpath(PosixPath(model.__name__))
        self.encrypted: bool = "secret" in model.__name__.lower()

    @property
    def state(self) -> Dict:
        try:
            resp = clients.ssm.get_parameter(
                Name=str(self.path), WithDecryption=self.encrypted
            )
            return json.loads(AwsSSMParam(**resp["Parameter"]).Value)
        except clients.ssm.exceptions.ParameterNotFound:
            return json.loads("{}")

    # TODO: this probably could use a rename
    @property
    def parameters(self) -> VALID_MODELS:
        return self.model(**self.state)

    def _write_parameters(self, dict: Dict) -> VALID_MODELS:
        params = {}
        params["Name"] = str(self.path)
        params["Value"] = self.model.construct(**dict).json()
        params["Overwrite"] = True
        params["Tier"] = "Standard"
        params["Type"] = "SecureString" if self.encrypted else "String"
        if params["Type"] == "SecureString":
            params["KeyId"] = self.kms_key_id
        clients.ssm.put_parameter(**params)
        return self._read()

    def _read(self) -> VALID_MODELS:
        return self.model.construct(**self.state)

    def set(self, key: str, value: Union[Json, str]) -> Table:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = value

        merged = self.state | {key: parsed}
        self._write_parameters(merged)
        return self.ls()

    def rm(self, key: str) -> Table:
        mutated = self.state.copy()
        try:
            del mutated[key]
            self._write_parameters(mutated)
        except KeyError:
            pass
        return self.ls()

    def export_defaults(self) -> None:
        self._write_parameters(self.parameters.dict())

    def clear(self) -> Table:
        try:
            clients.ssm.delete_parameter(Name=str(self.path))
        except clients.ssm.exceptions.ParameterNotFound:
            pass
        return self.ls()

    def validate(self) -> List[ValidationErrorInfo]:
        try:
            self.parameters
            return []
        except ValidationError as e:
            errors = []
            for error in e.errors():
                error = cast(Dict, error)
                errors.append(ValidationErrorInfo(key=error["loc"][0], **error))
            return errors

    def ls(self) -> Table:
        data = self._read()
        schema = data.schema()
        properties = schema["properties"]
        validations = self.validate()
        columns = list(StoreTableRow.schema()["properties"].keys())
        table = Table(*columns, box=box.SIMPLE)
        rows: List[StoreTableRow] = []

        # add rows found in schema
        for key, meta in properties.items():
            desc = meta["description"] if "description" in meta else None
            rows.append(
                StoreTableRow(key=key, value=None, description=desc, validation=None)
            )

        # populate existent values for properties defined in schema
        for row in rows:
            for key, value in data.dict().items():
                if row.key == key:
                    row.value = value

        # add rows for data _not_ in schema
        for key, value in data.dict().items():
            if not any([row.key == key for row in rows]):
                rows.append(
                    StoreTableRow(
                        key=key, value=value, description=None, validation=None
                    )
                )

        # populate validation information for each row
        for row in rows:
            for validation in validations:
                if row.key == validation.key:
                    row.validation = f"[red]{validation.msg}[/red]"

        # dump it into a renderable table object
        for row in rows:
            values = list(row.dict().values())
            values = [str(v) for v in values]
            table.add_row(*values)

        return table
