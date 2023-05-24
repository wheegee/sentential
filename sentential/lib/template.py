from shutil import copy
from textwrap import shorten
from os import makedirs
from typing import Any, Dict, Optional
from rich.table import Table, box
from pathlib import PosixPath
from os.path import dirname, abspath, exists
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template
from sentential.lib.shapes import SNTL_ENTRY_VERSION, derive_paths
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Envs
from pydantic import BaseModel
from typing import cast


PACKAGE_PATH = PosixPath(dirname(abspath(__file__))).parent


class Init:
    def __init__(self, repository_name: str, runtime: str) -> None:
        self.repository_name = repository_name
        self.runtime = runtime
        self.entry_version = SNTL_ENTRY_VERSION
        self.path = derive_paths()
        self.jinja = Environment(loader=FileSystemLoader(f"{PACKAGE_PATH}/templates"))

    def scaffold(self) -> None:
        if not exists(self.path.src):
            makedirs(self.path.src)

        self._write(self.jinja.get_template("Dockerfile"), self.path.dockerfile)

        copy(f"{PACKAGE_PATH}/templates/policy.json", self.path.policy)
        copy(f"{PACKAGE_PATH}/templates/shapes.py", self.path.shapes)

    def _write(self, template: Template, write_to: PosixPath) -> PosixPath:
        if not exists(write_to):
            with open(write_to, "w+") as f:
                f.writelines(
                    template.render(
                        repository_name=self.repository_name,
                        runtime=self.runtime,
                        entry_version=self.entry_version,
                        paths=self.path,
                    )
                )

        return write_to


class TemplateTableRow(BaseModel):
    interpolation: Any
    value: Optional[Any]


def flatten(kls: object) -> Dict[str, Any]:
    out = {}

    def flatten(x, name=""):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + ".")
        elif not hasattr(x, "__self__"):  # is not a method
            out[name[:-1]] = x

    flatten(kls)
    return out


class Policy:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.jinja = Environment(
            loader=FileSystemLoader("."), undefined=StrictUndefined
        )

    def render(self) -> str:
        template = self.jinja.get_template("policy.json")
        return template.render(
            context=self.ontology.context, env=cast(Envs, self.ontology.envs.parameters)
        )

    def available_data(self) -> Table:
        columns = list(TemplateTableRow.schema()["properties"].keys())
        table = Table(box=box.SIMPLE, *columns)
        envs = flatten(self.ontology.envs.parameters.dict())
        context = flatten(self.ontology.context.dict())

        for key, value in envs.items():
            table.add_row(*[f'"{{{{ env.{key} }}}}"', self._shorten(value)])

        for key, value in context.items():
            table.add_row(*[f'"{{{{ context.{key} }}}}"', self._shorten(value)])

        return table

    def _shorten(self, obj: Any) -> str:
        return shorten(str(obj), width=100, placeholder="...")
