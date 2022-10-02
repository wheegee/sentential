from sentential.lib.drivers.aws import AwsDriver
from sentential.lib.drivers.local import LocalDriver
from sentential.lib.ontology import Ontology
import polars as pl

class Joinery:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.local = LocalDriver(self.ontology)
        self.aws = AwsDriver(self.ontology)

    def imagery(self):
        self._aws_df()
    
    def _aws_df(self):
        aws_images = [ image.dict() for image in self.aws.images() ] 
        local_images = [ image.dict() for image in self.local.images() ] 
        aws_images = pl.from_dicts(aws_images)
        local_images = pl.from_dicts(local_images)
        print(aws_images.join(local_images, on="id", how="outer"))    

