import sys
from typing import Callable, List, Optional, cast

import click
from .colp import RGB, HEX


def check_hex(func: Callable[[List[HEX]], str]):
    def inner(*args: Optional[str]):
        colors: List[HEX] = []
        for arg in args:
            try:
                if not arg:
                    raise ValueError(func.__name__)
            except ValueError as f:
                click.secho(f"Error: Called {f} with empty color", fg="red", err=True)
                sys.exit(1)

            try:
                c = cast(HEX, HEX(arg))
            except ValueError:
                click.secho(
                    f"{arg} is not a valid hex color string", fg="red", err=True
                )
                sys.exit(1)

            colors.append(c)

        return func(colors)

    return inner


@check_hex
def make_alt_color(colors: List[HEX]) -> str:
    c = colors[0]
    return str(c.darker(1.25) if c.brightness() > 0.5 else c.brighter(1.25))


@check_hex
def make_alt_color_inverse(colors: List[HEX]) -> str:
    c = colors[0]
    return str(c.darker(1.1) if c.brightness() < 0.5 else c.brighter(1.1))


@check_hex
def make_orange_from_yellow(colors: List[HEX]) -> str:
    c = colors[0]
    return str(c.rotate(-15))


@check_hex
def make_brown_from_orange(colors: List[HEX]) -> str:
    c = colors[0]
    return str(c.rotate(-10).darker(1.1))


@check_hex
def make_average_color(colors: List[HEX]) -> str:
    try:
        a = colors[0]
        b = colors[1]
    except IndexError:
        click.secho(
            "make_average_color requires a list of two items", fg="red", err=True
        )
        sys.exit(1)

    return str(RGB((a.r + b.r) / 2, (a.g + b.g) / 2, (a.b + b.b) / 2).to(HEX))
