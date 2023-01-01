from typing import Dict, List, cast
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Provision


class AwsLambdaPublicUrlMount:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.resource_name = self.ontology.context.resource_name
        self.provision = cast(Provision, self.ontology.configs.parameters)

    def autocomplete(self) -> None:
        pass

    def mount(self) -> str:
        _ = self._put_permission()
        resp = self._put_url()
        return resp["FunctionUrl"]

    def umount(self) -> None:
        _ = self._delete_permission()
        _ = self._delete_url()

    def mounts(self) -> List[str]:
        resp = clients.lmb.get_function_url_config(FunctionName=self.resource_name)
        if "FunctionUrl" in resp:
            return [resp["FunctionUrl"]]
        else:
            return []

    def _put_url(self) -> Dict:
        function_name = self.ontology.context.resource_name
        config = {
            "FunctionName": function_name,
            "AuthType": self.provision.auth_type,
            "Cors": {
                "AllowHeaders": self.provision.allow_headers,
                "AllowMethods": self.provision.allow_methods,
                "AllowOrigins": self.provision.allow_origins,
                "ExposeHeaders": self.provision.expose_headers,
            },
        }

        try:
            clients.lmb.create_function_url_config(**config)
        except clients.lmb.exceptions.ResourceConflictException:
            clients.lmb.update_function_url_config(**config)

        return clients.lmb.get_function_url_config(FunctionName=function_name)

    def _put_permission(self) -> Dict:
        try:
            clients.lmb.remove_permission(
                FunctionName=self.resource_name,
                StatementId="FunctionURLAllowPublicAccess",
            )
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass

        return clients.lmb.add_permission(
            FunctionName=self.resource_name,
            StatementId="FunctionURLAllowPublicAccess",
            Action="lambda:InvokeFunctionUrl",
            Principal="*",
            FunctionUrlAuthType=self.provision.auth_type,
        )

    def _delete_url(self) -> None:
        try:
            clients.lmb.delete_function_url_config(FunctionName=self.resource_name)
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass

    def _delete_permission(self) -> None:
        try:
            clients.lmb.remove_permission(
                FunctionName=self.resource_name,
                StatementId="FunctionURLAllowPublicAccess",
            )
        except:
            pass
