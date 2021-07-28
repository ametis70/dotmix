import click

import dttr.config

from .cli import cli


@cli.group()
def config():
    """Configure dttr"""


@config.command("init")
@click.option(
    "--force",
    "-f",
    is_flag=True,
)
def init(force):
    """Initialize dttr config and data directory"""
    if force and click.confirm(
        "Are you sure you want to recreate the default config?", abort=True
    ):
        pass

    click.echo(f"{'Rei' if force else 'I'}ntializing config")
    dttr.config.create_config(force=force)
    click.echo("Creating data directories")
    dttr.config.scaffold_data_path()
