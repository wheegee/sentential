import typer
from rich import print
from sentential.lib.mounts.aws_event_schedule import AwsEventScheduleMount
from sentential.lib.ontology import Ontology

umount = typer.Typer()


@umount.command()
def schedule():
    """unmount lambda image from schedule"""
    AwsEventScheduleMount(Ontology()).umount()
