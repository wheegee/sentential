from sentential.lib.clients import clients
from types import SimpleNamespace
from tabulate import tabulate


class Store:
    def __init__(self, repository_name: str, kms_key_id: str = None):
        self.repository_name = repository_name
        self.kms_key_id = kms_key_id
        if kms_key_id is not None:
            self.type = "SecureString"
        else:
            self.type = "String"

    def write(self, key: str, value: str):
        kwargs = {
            "Name": f"/{self.repository_name}/{key.lower()}",
            "Value": value,
            "Type": self.type,
            "Overwrite": True,
            "Tier": "Standard",
        }

        if self.kms_key_id:
            kwargs["KeyId"] = self.kms_key_id

        return clients.ssm.put_parameter(**kwargs)

    def fetch(self):
        return clients.ssm.get_parameters_by_path(
            Path=f"/{self.repository_name}/",
            Recursive=True,
            WithDecryption=(self.kms_key_id is not None),
        )["Parameters"]

    def read(self):
        parameters = self.fetch()
        data = [
            [
                p["Name"].replace(f"/{self.repository_name}/", ""),
                p["Value"],
                p["Version"],
                p["LastModifiedDate"],
                p["Type"],
            ]
            for p in parameters
            if self.type == p["Type"]
        ]
        print(
            tabulate(
                data,
                headers=["Key", "Value", "Version", "LastModified", "Type"],
                tablefmt="tsv",
            )
        )

    def parameters(self):
        data = {
            p["Name"].replace(f"/{self.repository_name}/", ""): p["Value"]
            for p in self.fetch()
            if self.type == p["Type"]
        }
        return SimpleNamespace(**data)

    def delete(self, key: str):
        return clients.ssm.delete_parameter(Name=f"/{self.repository_name}/{key}")


class ConfigStore(Store):
    def __init__(self, repository_name: str):
        super().__init__(repository_name, None)


class SecretStore(Store):
    def __init__(self, repository_name: str, kms_key_id: str):
        super().__init__(repository_name, kms_key_id)
