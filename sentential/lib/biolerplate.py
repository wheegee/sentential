import os
from jinja2 import Environment, FileSystemLoader, Template
from os import makedirs
from os.path import exists
from pathlib import PosixPath, Path
from sentential.lib.facts import Facts
from enum import Enum
from shutil import copy

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
        self.facts = Facts(repository_name=repository_name)
        self.jinja = Environment(
            loader=FileSystemLoader(f"{PACKAGE_PATH}/../templates")
        )

    def ensure(self, runtime_image: str):
        self.facts.runtime = runtime_image
        if not exists(self.facts.path.src):
            makedirs(self.facts.path.src)
        self.sentential_file()
        self.dockerfile()
        self.wrapper()
        self.policy()

    def sentential_file(self):
        self._write(
            self.jinja.get_template("sentential.yml"), self.facts.path.sentential_file
        )

    def dockerfile(self):
        self._write(self.jinja.get_template("Dockerfile"), self.facts.path.dockerfile)

    def wrapper(self):
        self._write(self.jinja.get_template("wrapper.sh"), self.facts.path.wrapper)

    def policy(self):
        copy(f"{PACKAGE_PATH}/../templates/policy.json", self.facts.path.policy)

    def _write(self, template: Template, write_to: PosixPath) -> PosixPath:
        if not exists(write_to):
            with open(write_to, "w+") as f:
                f.writelines(template.render(facts=self.facts))

        return write_to
