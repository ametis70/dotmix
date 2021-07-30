import click

from dttr import colorscheme as lib

from .cli import cli


@cli.group()
def colorscheme():
    """Manage colorschemes"""


@colorscheme.command("list")
def list():
    """Show colorscheme names"""
    for colorscheme in lib.get_colorschemes().keys():
        click.secho(colorscheme, fg="blue", bold=True)


@colorscheme.command("show")
@click.argument("id")
def show(id):
    """Display colors from colorscheme"""
    lib.get_colorscheme_by_id(id).print_data()
