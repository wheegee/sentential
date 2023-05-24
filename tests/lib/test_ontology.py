import os
from pathlib import PosixPath
import pytest
import re
from os import environ, remove
from shutil import copyfile
from helpers import table_headers, table_body, rewrite
from pydantic import ValidationError
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import AWSCallerIdentity, Paths
from sentential.lib.exceptions import ContextError, ValidationError

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
        with pytest.raises(FileNotFoundError):
            ontology.context.repository_name


@pytest.mark.usefixtures("moto", "init", "ontology")
class TestStoreUndefined:
    def test_undefined(self, ontology: Ontology):
        assert (
            str(type(ontology.envs._read())) == "<class 'sentential.lib.shapes.Envs'>"
        )

    def test_ls(self, ontology: Ontology):
        table = ontology.envs.ls()
        headers = table_headers(table)
        body = table_body(table)
        assert ["key", "value", "description", "validation"] == headers
        assert len(body) == 0

    def test_set(self, ontology: Ontology):
        ontology.envs.set("key_1", "value_1")
        ontology.envs.set("key_2", "value_2")
        table = table_body(ontology.envs.set("key_3", "value_3"))
        assert ["key_1", "value_1", "None", "None"] in table
        assert ["key_2", "value_2", "None", "None"] in table
        assert ["key_3", "value_3", "None", "None"] in table

    def test_rm(self, ontology: Ontology):
        table = table_body(ontology.envs.rm("key_2"))
        assert ["key_2", "value_2", "None", "None"] not in table

    def test_clear(self, ontology: Ontology):
        body = table_body(ontology.envs.clear())
        assert len(body) == 0


@pytest.mark.usefixtures("moto", "init", "ontology")
class TestStoreDefined:
    def test_defined(self, ontology: Ontology):
        copyfile("./fixtures/shapes.py", "shapes.py")
        assert str(type(ontology.envs._read())) == "<class 'shapes.Envs'>"

    def test_read(self, ontology: Ontology):
        table = table_body(ontology.envs.ls())
        assert [
            "required_env",
            "None",
            "required",
            "[red]field required[/red]",
        ] in table
        assert ["optional_env", "default_value", "optional", "None"] in table

    def test_validation(self, ontology: Ontology):
        table = table_body(ontology.envs.set("required_env", "non-integer"))
        assert [
            "required_env",
            "non-integer",
            "required",
            "[red]value is not a valid integer[/red]",
        ] in table
        assert ["optional_env", "default_value", "optional", "None"] in table

    def test_extra_property(self, ontology: Ontology):
        table = table_body(ontology.envs.set("undefined_env", "undefined"))
        assert [
            "undefined_env",
            "undefined",
            "None",
            "[red]extra fields not permitted[/red]",
        ] in table

    def test_parameters_raises_when_failing(self, ontology: Ontology):
        with pytest.raises(ValidationError):
            ontology.envs.parameters

    def test_parameters_returns_when_passing(self, ontology: Ontology):
        ontology.envs.rm("undefined_env")
        ontology.envs.set("required_env", "123")
        assert ontology.envs.parameters.required_env == 123
        assert ontology.envs.parameters.optional_env == "default_value"

    def test_clear(self, ontology: Ontology):
        table = table_body(ontology.envs.clear())
        assert len(table) == 2
        assert [
            "required_env",
            "None",
            "required",
            "[red]field required[/red]",
        ] in table
        assert ["optional_env", "default_value", "optional", "None"] in table


@pytest.mark.usefixtures("moto", "init", "ontology")
class TestStoreProvision:
    def test_configs_type(self, ontology: Ontology):
        assert (
            str(type(ontology.configs._read()))
            == "<class 'sentential.lib.shapes.Configs'>"
        )

    def test_configs_read(self, ontology: Ontology):
        table = ontology.configs.ls()
        headers = table_headers(table)
        body = table_body(table)
        assert ["key", "value", "description", "validation"] == headers
        assert ["storage", "512", "ephemeral storage (mb)", "None"] in body

    def test_configs_write(self, ontology: Ontology):
        table = ontology.configs.set("storage", "1024")
        table = table_body(ontology.configs.ls())
        assert ["storage", "1024", "ephemeral storage (mb)", "None"] in table

    def test_configs_clear(self, ontology: Ontology):
        ontology.configs.clear()
        table = table_body(ontology.configs.ls())
        assert ["storage", "512", "ephemeral storage (mb)", "None"] in table

    def test_configs_write_bad_key(self, ontology: Ontology):
        ontology.configs.set("ram", "1024")
        with pytest.raises(ValidationError):
            ontology.configs.parameters
        ontology.configs.clear()

    def test_configs_write_bad_value(self, ontology: Ontology):
        ontology.configs.set("memory", "lots")
        with pytest.raises(ValidationError):
            ontology.configs.parameters
        ontology.configs.clear()


# TODO: this further implies the need for an epistemology seperate from ontology.
@pytest.mark.usefixtures("moto", "init", "ontology")
class TestStoreGlobalOps:
    def parameter_exists(self, prefix: PosixPath):
        resp = clients.ssm.describe_parameters(
            ParameterFilters=[
                {"Key": "Name", "Values": [str(prefix)]},
            ]
        )
        return len(resp["Parameters"]) == 1

    def test_undefined_export(self, ontology: Ontology):
        ontology.export_store_defaults()

        assert self.parameter_exists(ontology.args.path)
        assert self.parameter_exists(ontology.envs.path)
        assert self.parameter_exists(ontology.secrets.path)
        assert self.parameter_exists(ontology.tags.path)
        assert self.parameter_exists(ontology.configs.path)

    def test_defined_export_store_defaults_fails(self, ontology: Ontology):
        copyfile("./fixtures/shapes.py", "shapes.py")
        with pytest.raises(ValidationError):
            ontology.export_store_defaults()

    def test_defined_export_store_defaults_passes(self, ontology: Ontology):
        ontology.args.set("required_arg", "0")
        ontology.envs.set("required_env", "0")
        ontology.secrets.set("required_secret", "0")
        ontology.tags.set("required_tag", "0")
        ontology.export_store_defaults()
        assert ontology.args.parameters.required_arg == 0
        assert ontology.envs.parameters.required_env == 0
        assert ontology.secrets.parameters.required_secret == 0
        assert ontology.tags.parameters.required_tag == 0

    def test_clear_stores(self, ontology: Ontology):
        ontology.clear_stores()
        assert not self.parameter_exists(ontology.args.path)
        assert not self.parameter_exists(ontology.envs.path)
        assert not self.parameter_exists(ontology.secrets.path)
        assert not self.parameter_exists(ontology.tags.path)
        assert not self.parameter_exists(ontology.configs.path)
