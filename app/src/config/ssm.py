import os
from aws_lambda_powertools.utilities import parameters
from pathlib import Path

ssm_env = str(Path(f"/{os.getenv('PREFIX')}/runtime/"))
ssm_provider = parameters.SSMProvider()


def ssm():
    return ssm_provider.get_multiple(
        path=ssm_env,
        decrypt=True,
        recursive=True
    )
