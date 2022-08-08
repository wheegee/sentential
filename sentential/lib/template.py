import os
import json
from shutil import copy
from os import makedirs
from os.path import exists
from pathlib import PosixPath
from jinja2 import Environment, FileSystemLoader, Template
from sentential.lib.shapes.internal import derive_paths

PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))


class InitTime:
    def __init__(self, repository_name: str):
        self.repository_name = repository_name
        self.path = derive_paths()
        self.jinja = Environment(
            loader=FileSystemLoader(f"{PACKAGE_PATH}/../templates")
        )

    def scaffold(self, runtime_image: str):
        self.runtime = runtime_image
        if not exists(self.path.src):
            makedirs(self.path.src)
        if not exists(self.path.sntl):
            makedirs(self.path.sntl)
        self.dockerfile()
        self.wrapper()
        self.policy()

    def dockerfile(self):
        self._write(self.jinja.get_template("Dockerfile"), self.path.dockerfile)

    def wrapper(self):
        self._write(self.jinja.get_template("wrapper.sh"), self.path.wrapper)

    def policy(self):
        copy(f"{PACKAGE_PATH}/../templates/policy.json", self.path.policy)

    def _write(self, template: Template, write_to: PosixPath) -> PosixPath:
        if not exists(write_to):
            with open(write_to, "w+") as f:
                f.writelines(
                    template.render(
                        repository_name=self.repository_name,
                        runtime=self.runtime,
                        paths=self.path,
                    )
                )

        return write_to


# TODO: Turn this into a Spec deploy time templating system, extract from duplicate locations
# where it's currently implemented inline (local.py and aws.py)
# class DeployTime:
#     def __init__(self):
#         self.jinja = Environment(loader=FileSystemLoader("."))

# def policy(self) -> str:
#     return json.dumps(json.loads(self.template(str(facts.path.policy))))

# def template(self, template: PosixPath) -> str:
#     return self.jinja.get_template(template).render(facts=facts, config=)
