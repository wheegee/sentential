import botocore.exceptions
from python_on_whales.exceptions import DockerException


def gather_aws_exceptions() -> tuple:
    exceptions = []
    for key, value in sorted(botocore.exceptions.__dict__.items()):
        if isinstance(value, type):
            exceptions.append(getattr(botocore.exceptions, key))
    return tuple(exceptions)


AWS_EXCEPTIONS = gather_aws_exceptions()


class SntlException(BaseException):
    pass


class ShapeError(SntlException):
    pass


class AwsDriverError(SntlException):
    pass


class LocalDriverError(SntlException):
    pass


class ContextError(SntlException):
    pass


class StoreError(SntlException):
    pass


class JoineryError(SntlException):
    pass


class ApiGatewayResourceNotFound(SntlException):
    pass


class ArchitectureDiscoveryError(SntlException):
    pass
