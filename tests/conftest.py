import pytest
from fixtures.moto import moto
from fixtures.sntl import invoke, init
from tests.fixtures.ecr import mock_repo
from tests.fixtures.drivers import aws_ecr_driver, aws_lambda_driver, local_images_driver, local_lambda_driver
from tests.fixtures.common import cwi, ontology
