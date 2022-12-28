import boto3
from os import getenv
from python_on_whales import docker
from sentential.lib.exceptions import AWS_EXCEPTIONS

boto3_config = {"none": {}, "test": {"endpoint_url": "http://localhost:5000"}}


class Clients:
    def __init__(self, env: str = getenv("SENTENTIAL_ENV", "none")) -> None:
        self.boto3 = boto3
        self.lmb = boto3.client("lambda", **boto3_config[env])
        self.iam = boto3.client("iam", **boto3_config[env])
        self.sts = boto3.client("sts", **boto3_config[env])
        self.ecr = boto3.client("ecr", **boto3_config[env])
        self.ssm = boto3.client("ssm", **boto3_config[env])
        self.kms = boto3.client("kms", **boto3_config[env])
        self.api_gw = boto3.client("apigatewayv2", **boto3_config[env])
        self.cloudwatch = boto3.client("logs", **boto3_config[env])
        self.docker = docker


try:
    clients = Clients()
except AWS_EXCEPTIONS as e:
    print(f"AWS: {e}")
    exit(1)
