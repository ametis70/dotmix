import click
import dttr


@click.group()
def cli():
    pass


@cli.group()
def config():
    """Configure dttr"""


@config.command("init")
def init():
    """Initialize dttr config and data directory"""
    click.echo("Intializing config and data directory")
    dttr.config.create_config()
    dttr.config.scaffold_data_path()
