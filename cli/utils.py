from typing import Callable, Dict

import click

from dotmix.data import DataClassType


def print_setting_names(func: Callable[[], Dict[str, DataClassType]]):
    click.echo("Name (ID)")
    for settings in func().values():
        click.secho(f"{settings.name} ({settings.id})", fg="blue", bold=True)
