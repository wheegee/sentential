from functools import wraps
from time import sleep
from typing import Any, List, Tuple, Union
from rich.table import Table


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


def table_headers(table: Table) -> List[str]:
    return [str(column.header) for column in table.columns]


def table_body(table: Table) -> List[List[Any]]:
    cells = [column._cells for column in table.columns]
    body = [list(row) for row in zip(*cells)]
    return body
