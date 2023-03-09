import pytest
from shutil import copyfile
from sentential.lib.shapes import Architecture
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.mounts.aws_event_schedule import AwsEventScheduleMount
from sentential.lib.exceptions import AWS_EXCEPTIONS
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
        self,
        aws_lambda_driver: AwsLambdaDriver,
        aws_ecr_driver: AwsEcrDriver,
    ):
        image = aws_ecr_driver.get_image()
        aws_lambda_driver.deploy(image, Architecture.system())
        function_name = aws_lambda_driver.ontology.context.resource_name
        function_arn = aws_lambda_driver.ontology.context.resource_arn

        cron_expression = "cron(0 20 * * ? *)"
        payload = '{"foo": "bar"}'
        AwsEventScheduleMount(aws_lambda_driver.ontology).mount(
            cron_expression, payload
        )

        schedule_expression = self.get_rule(function_name)["ScheduleExpression"]
        schedule_targets = self.get_targets(function_name)["Targets"]

        assert cron_expression == schedule_expression
        assert function_arn == schedule_targets[0]["Arn"]
        assert payload == schedule_targets[0]["Input"]

    def test_umount(
        self,
        aws_lambda_driver: AwsLambdaDriver,
    ):
        function_name = aws_lambda_driver.ontology.context.resource_name

        AwsEventScheduleMount(aws_lambda_driver.ontology).umount()

        with pytest.raises(AWS_EXCEPTIONS):  # this is a tad lame
            self.get_rule(function_name)
