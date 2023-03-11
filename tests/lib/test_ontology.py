import pytest
import re
from os import environ, remove
from shutil import copyfile

from helpers import table_headers, table_body, rewrite

from sentential.lib.ontology import Ontology
from sentential.lib.shapes import AWSCallerIdentity, Paths
from sentential.lib.store import ModeledStore, GenericStore
from sentential.lib.exceptions import StoreError, ContextError

# We should figure out how to clear these for all tests...
if "PARTITION" in environ:
    del environ["PARTITION"]

if "AWS_KMS_KEY_ALIAS" in environ:
    del environ["AWS_KMS_KEY_ALIAS"]


@pytest.mark.usefixtures("moto", "init", "invoke", "ontology")
class TestContext(object):
    def test_repository_name(self, ontology: Ontology):
        assert ontology.context.repository_name == "test"

    def test_account_id(self, ontology: Ontology):
        assert ontology.context.account_id == "123456789012"

    def test_kms_key_alias(self, ontology: Ontology):
        assert ontology.context.kms_key_alias == "aws/ssm"

    def test_kms_key_alias_via_env(self, ontology: Ontology):
        environ["AWS_KMS_KEY_ALIAS"] = "some_custom_key"
        assert ontology.context.kms_key_alias == "some_custom_key"
        del environ["AWS_KMS_KEY_ALIAS"]

    def test_kms_key_id(self, ontology: Ontology):
        assert re.match(r"^.{8}-.{4}-.{4}-.{4}-.{12}", ontology.context.kms_key_id)

    def test_kms_key_id_via_env(self, ontology: Ontology):
        environ["AWS_KMS_KEY_ALIAS"] = "doesnt_exist"
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
        assert (
            ontology.context.repository_url
            == "123456789012.dkr.ecr.us-west-2.amazonaws.com/test"
        )

    def test_registry_url(self, ontology: Ontology):
        assert (
            ontology.context.registry_url
            == "123456789012.dkr.ecr.us-west-2.amazonaws.com"
        )

    def test_resource_name(self, ontology: Ontology):
        partition = ontology.context.partition
        repo = ontology.context.repository_name
        assert ontology.context.resource_name == f"{partition}-{repo}"

    def test_ecr_rest_url(self, ontology: Ontology):
        host = ontology.context.registry_url
        repo = ontology.context.repository_name
        assert ontology.context.ecr_rest_url == f"https://{host}/v2/{repo}"

    def test_bad_dockerfile(self, ontology: Ontology):
        rewrite("./Dockerfile", "FROM", "FROM ubuntu")
        with pytest.raises(ContextError):
            ontology.context.repository_name

    def test_missing_dockerfile(self, ontology: Ontology):
        remove("./Dockerfile")
        with pytest.raises(ContextError):
            ontology.context.repository_name


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


@pytest.mark.usefixtures("moto", "init", "ontology")
class TestModeledStore:
    def test_envs_store_type(self, ontology: Ontology):
        copyfile("./fixtures/shapes.py", "shapes.py")
        assert isinstance(ontology.envs, ModeledStore)

    def test_envs_write_bad_key(self, ontology: Ontology):
        with pytest.raises(StoreError):
            ontology.envs.write("bad_env", ["value"])

    def test_envs_write_good_key(self, ontology: Ontology):
        ontology.envs.write("required_env", ["123"])
        table = ontology.envs.read()
        assert ["field", "value", "validation", "description"] == table_headers(table)
        assert ["required_env", "123", None, "required"] in table_body(table)
        assert ["optional_env", "default_value", None, "optional"] in table_body(table)

    def test_envs_clear(self, ontology: Ontology):
        ontology.envs.clear()
        table = ontology.envs.read()
        assert ["required_env", None, "field required", "required"] in table_body(table)
        assert ["optional_env", "default_value", None, "optional"] in table_body(table)


@pytest.mark.usefixtures("moto", "init", "ontology")
class TestInternalStore:
    def test_configs_type(self, ontology: Ontology):
        assert isinstance(ontology.configs, ModeledStore)

    def test_configs_read(self, ontology: Ontology):
        table = ontology.configs.read()
        assert ["field", "value", "validation", "description"] == table_headers(table)
        assert ["storage", "512", None, "ephemeral storage (mb)"] in table_body(table)

    def test_configs_write_bad_key(self, ontology: Ontology):
        with pytest.raises(StoreError):
            ontology.configs.write("ram", ["1024"])

    def test_configs_write_bad_value(self, ontology: Ontology):
        with pytest.raises(StoreError):
            ontology.configs.write("memory", ["lots"])

    def test_configs_write(self, ontology: Ontology):
        ontology.configs.write("storage", ["1024"])
        table = ontology.configs.read()
        assert ["storage", "1024", None, "ephemeral storage (mb)"] in table_body(table)

    def test_configs_clear(self, ontology: Ontology):
        ontology.configs.clear()
        table = ontology.configs.read()
        assert ["storage", "512", None, "ephemeral storage (mb)"] in table_body(table)
