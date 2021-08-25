from typing import Callable, List, Optional, cast

from pydantic import BaseModel

from dttr.utils import print_err
from dttr.vendor.colp import HEX, RGB


class Base16Colorscheme(BaseModel):
    base00: Optional[str]
    base01: Optional[str]
    base02: Optional[str]
    base03: Optional[str]
    base04: Optional[str]
    base05: Optional[str]
    base06: Optional[str]
    base07: Optional[str]
    base08: Optional[str]
    base09: Optional[str]
    base0A: Optional[str]
    base0B: Optional[str]
    base0C: Optional[str]
    base0D: Optional[str]
    base0E: Optional[str]
    base0F: Optional[str]


class TerminalColorscheme(BaseModel):
    bg: Optional[str]
    fg: Optional[str]
    color0: Optional[str]
    color1: Optional[str]
    color2: Optional[str]
    color3: Optional[str]
    color4: Optional[str]
    color5: Optional[str]
    color6: Optional[str]
    color7: Optional[str]
    color8: Optional[str]
    color9: Optional[str]
    color10: Optional[str]
    color11: Optional[str]
    color12: Optional[str]
    color13: Optional[str]
    color14: Optional[str]
    color15: Optional[str]


class ParsedColorschemes(BaseModel):
    terminal: TerminalColorscheme
    base16: Base16Colorscheme


class DttrColorscheme(BaseModel):
    bg: str
    light_bg: str
    selection: str
    comment: str
    dark_fg: str
    fg: str
    light_fg: str
    lighter_bg: str

    red: str
    orange: str
    yellow: str
    green: str
    blue: str
    cyan: str
    magenta: str
    brown: str

    alt_red: str
    alt_orange: str
    alt_yellow: str
    alt_green: str
    alt_blue: str
    alt_cyan: str
    alt_magenta: str
    alt_brown: str


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
