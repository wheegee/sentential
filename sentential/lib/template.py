import os
import json
from shutil import copy
from os import makedirs
from os.path import exists
from pathlib import PosixPath
from jinja2 import Environment, FileSystemLoader, Template
from sentential.lib.facts import Facts

PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))


class InitTime:
    def __init__(self, repository_name: str):
        self.facts = Facts(repository_name=repository_name)
        self.jinja = Environment(
            loader=FileSystemLoader(f"{PACKAGE_PATH}/../templates")
        )

    def scaffold(self, runtime_image: str):
        self.facts.runtime = runtime_image
        if not exists(self.facts.path.src):
            makedirs(self.facts.path.src)
        if not exists(self.facts.path.sntl):
            makedirs(self.facts.path.sntl)
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


# TODO: Turn this into a Spec deploy time templating system, extract from duplicate locations
# where it's currently implemented inline (local.py and aws.py)
class DeployTime:
    def __init__(self):
        self.jinja = Environment(loader=FileSystemLoader("."))

    # def policy(self) -> str:
    #     return json.dumps(json.loads(self.template(str(facts.path.policy))))

    # def template(self, template: PosixPath) -> str:
    #     return self.jinja.get_template(template).render(facts=facts, config=)
