class SntlException(BaseException):
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
