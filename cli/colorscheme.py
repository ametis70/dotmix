import click

from .cli import cli

from dttr import colorscheme as lib


@cli.group()
def colorscheme():
    """Manage colorschemes"""


@colorscheme.command("list")
def cli_list():
    """Show colorscheme names"""
    for colorscheme in lib.get_colorschemes().keys():
        click.secho(colorscheme, fg="blue", bold=True)
