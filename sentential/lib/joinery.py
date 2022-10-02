from typing import List
from sentential.lib.drivers.aws import AwsDriver, AwsDriverError
from sentential.lib.drivers.local import LocalDriver, LocalDriverError
from sentential.lib.ontology import Ontology
from rich.table import Table
import polars as pl


class Joinery:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.local = LocalDriver(self.ontology)
        self.aws = AwsDriver(self.ontology)

    def local_images(self) -> Table:
        return self.to_table(self._local_df())

    def aws_images(self) -> Table:
        return self.to_table(self._aws_df())

    def deployments(self) -> Table:
        return self.to_table(self._deployed_df())

    def _deployed_df(self) -> pl.DataFrame:
        deployed = []
        for loc in [self.aws, self.local]:
            try:
                function = loc.deployed()
                deployed.append(function.dict(exclude={"image", "function_name"}))
            except LocalDriverError:
                pass
            except AwsDriverError:
                pass

        if deployed:
            return pl.from_dicts(deployed)
        else:
            return pl.DataFrame()

    def _local_df(self, drop: List[str] = []) -> pl.DataFrame:
        local_images = [image.dict() for image in self.local.images()]
        local_images = pl.from_dicts(local_images)
        if drop:
            local_images = local_images.drop(*drop)
        return local_images

    def _aws_df(self, drop: List[str] = []) -> pl.DataFrame:
        aws_images = [image.dict() for image in self.aws.images()]
        aws_images = pl.from_dicts(aws_images)
        if drop:
            aws_images = aws_images.drop(*drop)
        return aws_images

    def to_table(self, df: pl.DataFrame) -> Table:
        columns = df.columns
        table = Table(*columns)
        for row in df.rows():
            table.add_row(*[str(cell) for cell in row])
        return table
