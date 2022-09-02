from sentential.lib.const import SEMVER_REGEX
from sentential.lib.aws import Repository as AwsRepository
from sentential.lib.local import Repository as LocalRepository
from distutils.version import StrictVersion
from typing import List
import semantic_version as semver
from rich.table import Table
from rich import print
import polars as pl
import re


class Ontology:
    def __init__(self):
        self.aws = AwsRepository().df()
        self.local = LocalRepository().df()
        self.rgx = re.compile(SEMVER_REGEX)
        self.df = self.local.join(self.aws, on="Sha", how="outer")

    def _extract(self) -> pl.DataFrame:
        return self.df.select(
            [
                pl.col("Sha").alias("sha"),
                pl.col("Tag_right").alias("tag"),
                pl.col("Deployed").alias("deployed_local"),
                pl.col("Deployed_right").alias("deployed_aws"),
            ]
        )

    def _sort(self, df) -> pl.DataFrame:
        table = self._extract().drop_nulls("tag").drop_nulls("tag")
        rows = [row for row in table.rows() if self.rgx.match(row[1])]
        rows.sort(key=lambda row: StrictVersion(row[1]))
        rows = list(reversed(rows))
        # TODO: this is pretty lame, do it another way.
        sha = [row[0] for row in rows]
        tag = [row[1] for row in rows]
        deployed_local = [row[2] for row in rows]
        deployed_aws = [row[3] for row in rows]
        return pl.DataFrame(
            [sha, tag, deployed_local, deployed_aws], columns=table.columns
        )

    def _squash(self, df) -> pl.DataFrame:
        table = df.groupby("sha").agg_list()
        rows = table.to_dicts()
        for row in rows:
            row["tag"] = list(set(row["tag"]))
            row["deployed_local"] = any(row["deployed_local"])
            row["deployed_aws"] = any(row["deployed_aws"])
        # TODO: this is pretty lame, do it another way.
        sha = [row["sha"] for row in rows]
        tag = [row["tag"] for row in rows]
        deployed_local = [row["deployed_local"] for row in rows]
        deployed_aws = [row["deployed_aws"] for row in rows]
        return pl.DataFrame(
            [sha, tag, deployed_local, deployed_aws], columns=table.columns
        )

    def latest_semver(self) -> str:
        try:
            latest = list(self._sort(self._extract()).get_column("tag"))[0]
        except IndexError:
            latest = None
        return latest

    def next_build_semver(self) -> str:
        latest = self.latest_semver()
        if latest is None:
            latest = "0.0.0"
        return semver.Version(latest).next_patch()

    def semvers(self) -> List[str]:
        return list(self._sort(self._extract()).get_column("tag"))

    def sha_exists(self, sha) -> bool:
        table = self._squash(self._extract())
        for row in table.to_dicts():
            if row["sha"] == sha:
                return True
        return False

    def print(self) -> Table:
        df = self._squash(self._sort(self._extract()))
        table = Table(*df.columns)
        for row in df.rows():
            table.add_row(*[str(data) for data in row])

        print(table)
