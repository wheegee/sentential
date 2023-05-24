import pytest
import json
from shutil import copyfile
from helpers import table_headers, table_body
from sentential.lib.ontology import Ontology
from sentential.lib.template import Policy

@pytest.fixture(scope="class")
def policy() -> Policy:
    return Policy(Ontology())

@pytest.mark.usefixtures("moto", "init", "ontology", "policy")
class TestTemplate(object):
    def test_env(self, ontology: Ontology):
        copyfile("./fixtures/shapes_given.py", "shapes.py")
        assert str(type(ontology.envs._read())) == "<class 'shapes.Envs'>"
    
    def test_ls(self, policy: Policy):
        table = policy.available_data()
        assert table_headers(table) == ["interpolation", "value"]
        assert ['"{{ env.required_env }}"', '123'] in table_body(table)
        assert ['"{{ env.optional_env }}"', 'one, two, three'] in table_body(table)
        for row in table_body(table):
            assert "secret." not in row[0]

    def test_render(self, policy: Policy):
        policy_json = policy.render()
        policy_dict = json.loads(policy_json)
        assert policy_dict["Version"] == "2012-10-17"
        assert len(policy_dict["Statement"]) == 3