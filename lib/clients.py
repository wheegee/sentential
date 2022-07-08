from python_on_whales import docker
import boto3


class Clients:
    def __init__(self) -> None:
        self.lmb = boto3.client("lambda")
        self.iam = boto3.client("iam")
        self.sts = boto3.client("sts")
        self.ecr = boto3.client("ecr")
        self.docker = docker


clients = Clients()
