import click

from dttr.template import (
    get_templates,
    get_template_by_name,
    print_merged_template_files,
    get_merged_template_from_extends,
)

from .cli import cli


@cli.group()
def template():
    """Manage templates"""


@template.command("list")
def cli_list():
    """Show template names"""
    for template in get_templates():
        click.secho(template.name, fg="blue", bold=True)


@template.command("files")
@click.argument("template")
def cli_files(template):
    """List template files"""
    t = get_template_by_name(template)

    if t:
        print_merged_template_files(get_merged_template_from_extends(t))
