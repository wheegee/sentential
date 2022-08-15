from sentential.lib.clients import clients
from types import SimpleNamespace
from sentential.lib.facts import Factual
from tabulate import tabulate


class Store(Factual):
    def __init__(self, suffix: str):
        super().__init__()
        self.path = f"/{self.facts.partition}/{self.facts.repository_name}/{suffix}/"
        self.chamber_path = (
            f"{self.facts.partition}/{self.facts.repository_name}/{suffix}"
        )
        self.kms_key_id = self.facts.kms_key_id

    def write(self, key: str, value: str):
        kwargs = {
            "Name": f"{self.path}{key.lower()}",
            "Value": value,
            "Type": "SecureString",
            "Overwrite": True,
            "Tier": "Standard",
            "KeyId": self.kms_key_id,
        }

        return clients.ssm.put_parameter(**kwargs)

    def fetch(self):
        return clients.ssm.get_parameters_by_path(
            Path=self.path,
            Recursive=True,
            WithDecryption=True,
        )["Parameters"]

    def read(self):
        parameters = self.fetch()
        data = [
            [
                p["Name"].replace(self.path, ""),
                p["Value"],
                p["Version"],
                p["LastModifiedDate"],
            ]
            for p in parameters
        ]
        print(
            tabulate(
                data,
                headers=["Key", "Value", "Version", "LastModified"],
                tablefmt="tsv",
            )
        )

    def parameters(self):
        data = {p["Name"].replace(self.path, ""): p["Value"] for p in self.fetch()}
        return SimpleNamespace(**data)

    def delete(self, key: str):
        try:
            return clients.ssm.delete_parameter(Name=f"{self.path}{key}")
        except clients.ssm.exceptions.ParameterNotFound:
            pass


class Env(Store):
    def __init__(self):
        super().__init__("env")


class Arg(Store):
    def __init__(self):
        super().__init__("arg")
