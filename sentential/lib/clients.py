import boto3
from python_on_whales import docker


class Clients:
    def __init__(self) -> None:
        self.lmb = boto3.client("lambda")
        self.iam = boto3.client("iam")
        self.sts = boto3.client("sts")
        self.ecr = boto3.client("ecr")
        self.ssm = boto3.client("ssm")
        self.cloudwatch = boto3.client("logs")
        self.docker = docker


clients = Clients()
