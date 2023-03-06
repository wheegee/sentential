from typing import Dict, List, cast
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Provision


class AwsEventScheduleMount:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.resource_name = self.ontology.context.resource_name
        self.resource_arn = self.ontology.context.resource_arn
        self.provision = cast(Provision, self.ontology.configs.parameters)

    def autocomplete(self) -> None:
        pass

    def mount(self, schedule) -> str:
        resp = self._put_rule(schedule)
        _ = self._put_permission(resp["RuleArn"])
        _ = self._put_targets()
        return resp["RuleArn"]

    def umount(self) -> None:
        _ = self._delete_targets()
        _ = self._delete_permission()
        _ = self._delete_rule()

    def mounts(self) -> List[str]:
        resp = clients.lmb.get_function_url_config(FunctionName=self.resource_name)
        if "FunctionUrl" in resp:
            return [resp["FunctionUrl"]]
        else:
            return []

    def _put_rule(self, schedule) -> Dict:
        try:
            clients.ebr.delete_rule(Name=self.resource_name)
        except clients.ebr.exceptions.ResourceNotFoundException:
            pass

        return clients.ebr.put_rule(
            Name=self.resource_name,
            ScheduleExpression=f"cron({schedule})",
        )

    def _put_targets(self) -> None:
        try:
            clients.ebr.put_targets(
                Rule=self.resource_name,
                Targets=[
                    {
                        "Id": self.resource_name,
                        "Arn": self.resource_arn,
                    }
                ],
            )
        except clients.ebr.exceptions.ResourceNotFoundException:
            pass

    def _put_permission(self, rule_arn) -> Dict:
        try:
            clients.lmb.remove_permission(
                FunctionName=self.resource_name,
                StatementId="EventBridgeAllowInvoke",
            )
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass

        return clients.lmb.add_permission(
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
