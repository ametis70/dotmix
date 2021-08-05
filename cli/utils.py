from typing import Callable, Dict

import click

from dttr.utils import A


def print_setting_names(func: Callable[[], Dict[str, A]]):
    click.echo("Name (ID)")
    for settings in func().values():
        click.secho(f"{settings.name} ({settings.id})", fg="blue", bold=True)
