from typing import Dict, List, cast
from sentential.lib.mounts.spec import MountDriver
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Configs, EbrDescribeRuleResponse, EbrPutRuleResponse


class AwsEventScheduleMount(MountDriver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.resource_name = self.ontology.context.resource_name
        self.resource_arn = self.ontology.context.resource_arn
        self.provision = cast(Configs, self.ontology.configs.parameters)

    def autocomplete(self) -> None:
        pass

    def mount(self, schedule, payload) -> str:
        resp = self._put_rule(schedule)
        _ = self._put_permission(resp.RuleArn)
        _ = self._put_targets(payload)
        return f"mounted {schedule} to {self.resource_name}"

    def umount(self) -> None:
        _ = self._delete_targets()
        _ = self._delete_permission()
        _ = self._delete_rule()

    def mounts(self) -> List[str]:
        resp = clients.ebr.describe_rule(Name=self.resource_name)
        resp = EbrDescribeRuleResponse(**resp)
        if resp.ScheduleExpression:
            return [resp.ScheduleExpression]
        else:
            return []

    def _put_rule(self, schedule) -> EbrPutRuleResponse:
        resp = clients.ebr.put_rule(
            Name=self.resource_name,
            ScheduleExpression=schedule,
        )
        return EbrPutRuleResponse(**resp)

    def _put_targets(self, payload) -> None:
        try:
            clients.ebr.put_targets(
                Rule=self.resource_name,
                Targets=[
                    {
                        "Id": self.resource_name,
                        "Arn": self.resource_arn,
                        "Input": payload,
                    }
                ],
            )
        except clients.ebr.exceptions.ResourceNotFoundException:
            pass

    def _put_permission(self, rule_arn) -> None:
        try:
            clients.lmb.remove_permission(
                FunctionName=self.resource_name,
                StatementId="EventBridgeAllowInvoke",
            )
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass

        clients.lmb.add_permission(
            FunctionName=self.resource_name,
            StatementId="EventBridgeAllowInvoke",
            Action="lambda:InvokeFunction",
            Principal="events.amazonaws.com",
            SourceArn=rule_arn,
        )

    def _delete_rule(self) -> None:
        try:
            clients.ebr.delete_rule(Name=self.resource_name)
        except clients.ebr.exceptions.ResourceNotFoundException:
            pass

    def _delete_targets(self) -> None:
        try:
            clients.ebr.remove_targets(
                Rule=self.resource_name, Ids=[self.resource_name]
            )
        except clients.ebr.exceptions.ResourceNotFoundException:
            pass

    def _delete_permission(self) -> None:
        try:
            clients.lmb.remove_permission(
                FunctionName=self.resource_name,
                StatementId="EventBridgeAllowInvoke",
            )
        except:
            pass
