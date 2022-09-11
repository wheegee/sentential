from sentential.lib.const import PACKAGE_PATH
from sentential.lib.shapes.internal import derive_paths
from shutil import copy
from os import makedirs
from os.path import exists
from pathlib import PosixPath
from jinja2 import Environment, FileSystemLoader, Template


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
        self.dockerfile()
        self.policy()
        self.shapes()

    def dockerfile(self):
        self._write(self.jinja.get_template("Dockerfile"), self.path.dockerfile)

    def policy(self):
        copy(f"{PACKAGE_PATH}/../templates/policy.json", self.path.policy)

    def shapes(self):
        copy(f"{PACKAGE_PATH}/../templates/shapes.py", self.path.shapes)

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
