import ast
import polars as pl
from builtins import BaseException
from pydantic import BaseModel, ValidationError, Extra, Field
from typing import Any, List, Tuple, Union, cast

#
# User Driven Shapes
#

ALLOWED_LIST_TYPES = [List[str], List[int], List[float]]
ALLOWED_TYPES = [str, int, float] + ALLOWED_LIST_TYPES


class ShaperError(BaseException):
    pass


class Shaper(BaseModel):
    class Config:
        extra = Extra.forbid

    @classmethod
    def validate_field_value(cls, field: str, value: Any):
        try:
            validations = cls.constrained_validation_df({field: value})
        except KeyError as e:
            raise ShaperError(
                f"invalid key, valid options {list(cls.__fields__.keys())}"
            )

        validations = validations.filter(pl.col("field") == field)

        if len(validations) != 1:
            raise ShaperError(
                f"number of validations for {field} must be 1, found {len(validations)}"
            )

        validation = validations.row(0)
        (key, validation_error) = cast(Tuple[str, str], validation)

        if validation_error is not None:
            raise ValueError(validation_error)

    @classmethod
    def constrained_parse_obj(cls, data: dict):
        for (name, field) in cls.__fields__.items():
            # disallow types
            if field.outer_type_ not in ALLOWED_TYPES:
                raise ShaperError(f"disallowed type {field.outer_type_}")

        # If data is populating from ssm, it's always a string.
        # A list is stored in ssm as "[ 'some', 'list' ]"
        # Use knowledge that the field is a list, and ast.literal_eval
        # to bring it back to a python list, pydantic will coerce what's within
        for field in cls.__fields__.values():
            if field.outer_type_ in ALLOWED_LIST_TYPES:
                if field.name in data and type(data[field.name]) is str:
                    data[field.name] = ast.literal_eval(data[field.name])

        return cls(**data)

    @classmethod
    def type_constraints_df(cls):
        columns = [("field", pl.Utf8), ("type_check", pl.Utf8)]
        fields = [name for name in cls.__fields__.keys()]
        type_checks = [
            f"disallowed type {f.outer_type_}"
            if f.outer_type_ not in ALLOWED_TYPES
            else None
            for f in list(cls.__fields__.values())
        ]

        return pl.DataFrame(
            [
                fields,
                type_checks,
            ],
            columns=columns,
        )

    @classmethod
    def validation_df(cls, data: dict):
        columns = [("field", pl.Utf8), ("value_check", pl.Utf8)]
        fields = [name for name in cls.__fields__.keys()]
        try:
            cls.constrained_parse_obj(data)
            return pl.DataFrame([fields, [None for f in fields]], columns=columns)
        except ValidationError as e:
            locations = [map(str, e["loc"]) for e in e.errors()]
            locations = ["/".join(loc) for loc in locations]
            messages = [e["msg"] for e in e.errors()]
            return pl.DataFrame(
                [locations, messages],
                columns=columns,
            )

    @classmethod
    def constrained_validation_df(cls, data: dict):
        type_constraints = cls.type_constraints_df()
        validations = cls.validation_df(data)

        df = type_constraints.join(validations, on="field", how="outer")
        df = df.with_columns(
            [
                (pl.col("type_check").fill_null(pl.col("value_check"))).alias(
                    "validation"
                )
            ]
        )
        return df.select([pl.col("field"), pl.col("validation")])

    @classmethod
    def schema_df(cls):
        fields = list(cls.schema()["properties"].keys())
        properties = list(cls.schema()["properties"].values())
        defaults = [str(p["default"]) if "default" in p else None for p in properties]
        descriptions = [
            p["description"] if "description" in p else None for p in properties
        ]
        columns = [("field", pl.Utf8), ("default", pl.Utf8), ("description", pl.Utf8)]
        return pl.DataFrame(
            [
                fields,
                defaults,
                descriptions,
            ],
            columns=columns,
        )
