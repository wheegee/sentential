from sentential.lib.clients import clients
from types import SimpleNamespace
from sentential.lib.facts import Facts, Factual
from tabulate import tabulate


class Store(Factual):
    def __init__(self, partition: str, kms_key_id: str = None):
        super().__init__()
        self.repository_name = self.facts.repository_name
        self.partition = partition
        self.path = f"/{self.partition}/{self.repository_name}/"
        self.kms_key_id = kms_key_id
        if kms_key_id is not None:
            self.type = "SecureString"
        else:
            self.type = "String"

    def write(self, key: str, value: str):
        kwargs = {
            "Name": f"{self.path}{key.lower()}",
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
            Path=self.path,
            Recursive=True,
            WithDecryption=(self.kms_key_id is not None),
        )["Parameters"]

    def read(self):
        parameters = self.fetch()
        data = [
            [
                p["Name"].replace(self.path, ""),
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
            p["Name"].replace(self.path, ""): p["Value"]
            for p in self.fetch()
            if self.type == p["Type"]
        }
        return SimpleNamespace(**data)

    def delete(self, key: str):
        return clients.ssm.delete_parameter(Name=f"{self.path}{key}")


class ConfigStore(Store):
    def __init__(self, partition: str):
        super().__init__(partition, None)


class SecretStore(Store):
    def __init__(self, partition: str):
        # TODO: this Facts() usage is muy backwards, needs to be more like Partitions when Partitions is corrected
        super().__init__(partition, Facts().kms_key_id)
