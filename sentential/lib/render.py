import json
from jinja2 import Environment, FileSystemLoader, Template
from pathlib import PosixPath
from sentential.lib.facts import Facts


class Render:
    def __init__(self, facts: Facts):
        self.facts = facts
        self.jinja = Environment(loader=FileSystemLoader("."))

    def policy(self) -> dict:
        return json.loads(self.template(str(self.facts.path.policy)))

    def template(self, template: PosixPath) -> str:
        return self.jinja.get_template(template).render(facts=self.facts)
