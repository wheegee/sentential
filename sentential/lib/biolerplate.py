import os
from jinja2 import Environment, FileSystemLoader, Template
from os import makedirs
from os.path import exists
from pathlib import PosixPath, Path
from sentential.lib.config import Config
from enum import Enum

PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

# https://gallery.ecr.aws/lambda?page=1
class Runtimes(Enum):
    python = "python"
    dotnet = "dotnet"
    java = "java"
    go = "go"
    nodejs = "nodejs"
    provided = "provided"
    ruby = "ruby"


class BoilerPlate:
    def __init__(self, repository_name: str):
        self.config = Config(repository_name=repository_name)
        self.jinja = Environment(
            loader=FileSystemLoader(f"{PACKAGE_PATH}/../templates")
        )

    def ensure(self, runtime_image: str):
        if not exists(Path(self.config.path.src)):
            makedirs(self.config.path.src)
        self.dockerfile(runtime_image)
        self.wrapper()
        self.policy()

    def dockerfile(self, image: str):
        self.config.runtime = image
        self._write(self.jinja.get_template("Dockerfile"), self.config.path.dockerfile)

    def wrapper(self):
        self._write(self.jinja.get_template("wrapper.sh"), self.config.path.wrapper)

    def policy(self):
        self._write(self.jinja.get_template("policy.json"), self.config.path.policy)

    def _write(self, template: Template, write_to: PosixPath) -> PosixPath:
        if not exists(write_to):
            with open(write_to, "w+") as f:
                f.writelines(template.render(config=self.config))

        return write_to
