from typing import Callable, Dict

import click

from dttr.utils import AbstractConfigType


def print_setting_names(func: Callable[[], Dict[str, AbstractConfigType]]):
    click.echo("Name (ID)")
    for settings in func().values():
        click.secho(f"{settings.name} ({settings.id})", fg="blue", bold=True)