from functools import wraps
from time import sleep


class RetryWrapperError(BaseException):
    pass


def retry(
    times=10,
    ExceptionToCheck=AssertionError,
):
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries = times
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    sleep(1)
                    mtries -= 1
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
