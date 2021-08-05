from typing import Callable, List, Optional, cast

from dttr.utils import print_err

from .colp import HEX, RGB


def check_hex(func: Callable[[List[HEX]], str]):
    def inner(*args: Optional[str]):
        colors: List[HEX] = []
        for arg in args:
            try:
                if not arg:
                    raise ValueError(func.__name__)
            except ValueError as f:
                print_err(f"Called {f} with empty color", True)

            try:
                c = cast(HEX, HEX(arg))
            except ValueError:
                print_err(f"{arg} is not a valid hex color string", True)

            colors.append(c)  # type: ignore

        return func(colors)

    return inner


@check_hex
def normalize(colors: List[HEX]) -> str:
    return str(colors[0])


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
        print_err("make_average_color requires a list of two items", True)

    return str(
        RGB((a.r + b.r) / 2, (a.g + b.g) / 2, (a.b + b.b) / 2).to(HEX)  # type: ignore
    )
