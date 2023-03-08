import pytest
from shutil import copyfile
from sentential.lib.shapes import Architecture
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.exceptions import AWS_EXCEPTIONS
from sentential.lib.mounts.aws_event_schedule import AwsEventScheduleMount
from sentential.lib.clients import clients


@pytest.mark.usefixtures(
    "moto", "init", "ontology", "mock_repo", "aws_lambda_driver", "aws_ecr_driver"
)
class TestAwsEventScheduleMount:
    def get_rule(self, rule_name: str):
        return clients.ebr.describe_rule(Name=rule_name)

    def get_targets(self, rule_name: str):
        return clients.ebr.list_targets_by_rule(Rule=rule_name)

    def test_mount(
        self, aws_lambda_driver: AwsLambdaDriver, aws_ecr_driver: AwsEcrDriver
    ):
        cron_expression = "cron(0 20 * * ? *)"
        payload = '{"foo": "bar"}'
        image = aws_ecr_driver.get_image()
        aws_lambda_driver.deploy(image, Architecture.system())
        AwsEventScheduleMount(aws_lambda_driver.ontology).mount(cron_expression, payload)
        schedule_expression = self.get_rule(
            aws_lambda_driver.ontology.context.resource_name
        )["ScheduleExpression"]
        schedule_targets = self.get_targets(
            aws_lambda_driver.ontology.context.resource_name
        )["Targets"]
        assert cron_expression == schedule_expression
        assert (
            aws_lambda_driver.ontology.context.resource_arn
            == schedule_targets[0]["Arn"]
        )
        assert payload == schedule_targets[0]["Input"]
