from os import environ, remove
from shutil import copyfile
import pytest
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import AWSCallerIdentity, Paths
from sentential.lib.store import ModeledStore, GenericStore
from sentential.lib.exceptions import StoreError, ContextError
from helpers import table_headers, table_body


@pytest.mark.usefixtures("moto", "init", "invoke", "ontology")
class TestContext(object):
    def test_repository_name_no_dockerfile(self, ontology: Ontology, invoke):
        remove("./Dockerfile")
        with pytest.raises(ContextError):
            ontology.context.repository_name
        invoke(["init", "testing", "python"])

    def test_repository_name_malformed_dockerfile(self, ontology: Ontology, repo, project, invoke):
        copyfile(f"{project}/tests/fixtures/files/Dockerfile.malformed", f"{repo.name}/Dockerfile")
        with pytest.raises(ContextError):
            ontology.context.repository_name
        remove("./Dockerfile")
        invoke(["init", "testing", "python"])

    def test_repository_name(self, ontology: Ontology):
        assert ontology.context.repository_name == "testing"

    def test_account_id(self, ontology: Ontology):
        assert ontology.context.account_id == "123456789012"


    def test_kms_key_alias(self, ontology: Ontology):
        assert ontology.context.kms_key_alias == "aws/ssm"


    def test_kms_key_alias_via_env(self, ontology: Ontology):
        environ["AWS_KMS_KEY_ALIAS"]="some_custom_key"
        assert ontology.context.kms_key_alias == "some_custom_key"
        del environ["AWS_KMS_KEY_ALIAS"]


    def test_kms_key_id(self, ontology: Ontology):
        assert ontology.context.kms_key_id == "b9b07f4b-97ba-48c8-b74e-54bce06562cf"


    def test_kms_key_id_via_env(self, ontology: Ontology):
        environ["AWS_KMS_KEY_ALIAS"]="doesnt_exist"
        with pytest.raises(ContextError):
            ontology.context.kms_key_id
        del environ["AWS_KMS_KEY_ALIAS"]


    def test_caller_identity(self, ontology: Ontology):
        assert isinstance(ontology.context.caller_identity, AWSCallerIdentity)


    def test_partition(self, ontology: Ontology):
        assert ontology.context.partition == "AKIAIOSFODNN7EXAMPLE"


    def test_region(self, ontology: Ontology):
        # TODO: consider this, probably best to test "one of" all valid regions
        assert ontology.context.region == "us-west-2"


    def test_path(self, ontology: Ontology):
        assert isinstance(ontology.context.path, Paths)


    def test_repository_url(self, ontology: Ontology):
        assert ontology.context.repository_url == "123456789012.dkr.ecr.us-west-2.amazonaws.com/testing"


    def test_registry_url(self, ontology: Ontology):
        assert ontology.context.registry_url == "123456789012.dkr.ecr.us-west-2.amazonaws.com"

@pytest.mark.usefixtures("moto", "init", "shapes", "ontology")
class TestModeledStore:
    def test_envs_store_type(self, ontology: Ontology):
        assert isinstance(ontology.envs, ModeledStore)

    def test_envs_write_bad_key(self, ontology: Ontology):
        with pytest.raises(StoreError):
            ontology.envs.write("bad_env", ["value"])
    
    def test_envs_write_good_key(self, ontology: Ontology):
        ontology.envs.write("required_env", ["123"])
        table = ontology.envs.read()
        assert ["field", "value", "validation", "description"] == table_headers(table)
        assert ['required_env', '123', 'None', 'required'] in table_body(table)
        assert ['optional_env', 'default_value', 'None', 'optional'] in table_body(table)
    
    def test_envs_clear(self, ontology: Ontology):
        ontology.envs.clear()
        table = ontology.envs.read()
        assert ['required_env', 'None', 'field required', 'required'] in table_body(table)
        assert ['optional_env', 'default_value', 'None', 'optional'] in table_body(table)

@pytest.mark.usefixtures("moto", "init", "shapes", "ontology")
class TestInternalStore:
    def test_configs_type(self, ontology: Ontology):
        assert isinstance(ontology.configs, ModeledStore)
    
    def test_configs_read(self, ontology: Ontology):
        table = ontology.configs.read()
        assert ["field", "value", "validation", "description"] == table_headers(table)
        assert ["storage", "512", "None", "ephemeral storage (mb)"] in table_body(table)

    def test_configs_write_bad_key(self, ontology: Ontology):
        with pytest.raises(StoreError):
            ontology.configs.write("ram", ["1024"])

    def test_configs_write_bad_value(self, ontology: Ontology):
        with pytest.raises(StoreError):
            ontology.configs.write("memory", ["lots"])
    
    def test_configs_write(self, ontology: Ontology):
        ontology.configs.write("storage", ["1024"])
        table = ontology.configs.read()
        assert ["storage", "1024", "None", "ephemeral storage (mb)"] in table_body(table)
    
    def test_configs_clear(self, ontology: Ontology):
        ontology.configs.clear()
        table = ontology.configs.read()
        assert ["storage", "512", "None", "ephemeral storage (mb)"] in table_body(table)

@pytest.mark.usefixtures("moto", "init", "ontology")
class TestGenericStore:
    def test_envs_store_type(self, ontology: Ontology):
        assert isinstance(ontology.envs, GenericStore)

    def test_envs_read(self, ontology):
        table = ontology.envs.read()
        assert table.row_count == 0
            
    def test_envs_write(self, ontology: Ontology):
        ontology.envs.write("test_1", ["value_1"])
        ontology.envs.write("test_2", ["value_2"])
        table = ontology.envs.read()
        assert ["field", "value"] == table_headers(table)
        assert ["test_1", "value_1"] in table_body(table)
        assert ["test_2", "value_2"] in table_body(table)
    
    def test_envs_clear(self, ontology: Ontology):
        ontology.envs.clear()
        table = ontology.envs.read()
        assert [] == table_body(table)