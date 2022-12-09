import typer
from sentential.lib.clients import clients
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.template import Init
from sentential.lib.shapes import Runtimes
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.semver import SemVer
from sentential.lib.ontology import Ontology
from sentential.lib.joinery import Joinery
from sentential.lib.shapes import CURRENT_WORKING_IMAGE_TAG
from rich import print

root = typer.Typer()


@root.command()
def init(repository_name: str, runtime: Runtimes):
    """initialize sentential project"""
    aws_supported_image = f"public.ecr.aws/lambda/{runtime.value}:latest"
    Init(repository_name, aws_supported_image).scaffold()


@root.command()
def build():
    """build lambda image"""
    docker = LocalImagesDriver(Ontology())
    print(docker.build(CURRENT_WORKING_IMAGE_TAG))


@root.command()
def publish(major: bool = typer.Option(False), minor: bool = typer.Option(False)):
    """publish lambda image"""
    ontology = Ontology()
    ecr = AwsEcrDriver(ontology)
    docker = LocalImagesDriver(ontology)
    tag = SemVer(ecr.images()).next(major, minor)
    print(docker.push(tag))


@root.command()
def login():
    """login to ecr"""
    clients.docker.login_ecr()


@root.command()
def ls():
    """list image information"""
    print(Joinery(Ontology()).list(["tags", "uri"]))


@root.command()
def clean(remote: bool = typer.Option(False)):
    """clean images"""
    ontology = Ontology()
    ecr = AwsEcrDriver(ontology)
    docker = LocalImagesDriver(ontology)

    for image in docker.images():
        clients.docker.container.remove("sentential", force=True)
        clients.docker.image.remove(image.id, force=True)

    for builder in clients.docker.buildx.list():
        if builder.name == "sentential-builder":
            clients.docker.buildx.use(builder)
            clients.docker.buildx.prune(all=True)

    if remote:
        image_details = ecr._image_details()
        manifest_digests = [
            {"imageDigest": detail.imageId.imageDigest} for detail in image_details
        ]
        clients.ecr.batch_delete_image(
            repositoryName=ontology.context.repository_name, imageIds=manifest_digests
        )
