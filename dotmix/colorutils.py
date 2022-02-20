"""This module contains the utilitary models and functions needed by
:mod:`dotmix.colorscheme` """

from typing import Any, Callable, Optional, TypeVar, cast

from pydantic import BaseModel

from dotmix.utils import print_err
from dotmix.vendor.colp import HEX, RGB


class Base16Colorscheme(BaseModel):
    """Model for a Base16 colorscheme definition.

    Check the `Base16 website <http://www.chriskempson.com/projects/base16/>`_ to learn
    more.

    :param base00: Default background
    :param base01: Lighter Background (Used for status bars, line number and folding
        marks)
    :param base02: Selection Background
    :param base03: Comments, Invisibles, Line Highlighting
    :param base04: Dark Foreground (Used for status bars)
    :param base05: Default Foreground, Caret, Delimiters, Operators
    :param base06: Light Foreground (Not often used)
    :param base07: Light Background (Not often used)
    :param base08: Variables, XML Tags, Markup Link Text, Markup Lists, Diff Deleted
    :param base09: Integers, Boolean, Constants, XML Attributes, Markup Link Url
    :param base0A: Classes, Markup Bold, Search Text Background
    :param base0B: Strings, Inherited Class, Markup Code, Diff Inserted
    :param base0C: Support, Regular Expressions, Escape Characters, Markup Quotes
    :param base0D: Functions, Methods, Attribute IDs, Headings
    :param base0E: Keywords, Storage, Selector, Markup Italic, Diff Changed
    :param base0F: Deprecated, Opening/Closing Embedded Language Tags, e.g. ``<?php ?>``
    """

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
    """Model for a Terminal colorscheme definition.

    This corresponds to the 16 colors that terminal emulators always used for
    historical reasons (dating back to when EGA/VGA were a thing).

    Color numbers are based off the order of the
    `ANSI escape codes <https://en.wikipedia.org/wiki/ANSI_escape_code>`_.

    Modern terminal emulators also allow to define a different background and
    foreground colors and these can be specified using the ``bg`` and ``fg``
    fields respectively

    :param bg: Background (black)
    :param fg: Foreground (white)
    :param color0: Black
    :param color1: Red
    :param color2: Green
    :param color3: Yellow
    :param color4: Blue
    :param color5: Magenta
    :param color6: Cyan
    :param color7: White
    :param color8: Bright black (gray)
    :param color9: Bright Red
    :param color10: Bright Green
    :param color11: Bright Yellow
    :param color12: Bright Blue
    :param color13: Bright Magenta
    :param color14: Bright Cyan
    :param color15: Bright White
    """

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
    """This model holds a definition of every the possible colorscheme model"""

    terminal: TerminalColorscheme
    base16: Base16Colorscheme


class DotmixColorscheme(BaseModel):
    """Model for the dotmix colorscheme.

    Depending on the input colorscheme (e.g terminal or base16), some of these colors
    may be generated from others as needed.

    These are the colors that are made available to the templating engine.
    """

    bg: str
    light_bg: str
    selection: str
    comment: str
    dark_fg: str
    fg: str
    light_fg: str
    lighter_fg: str

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


HexSafeFunction = TypeVar(
    "HexSafeFunction",
    bound=Callable[..., Any],
)
"""Type for functions that take hexadecimal color codes as inputs"""


def check_hex(func: HexSafeFunction) -> HexSafeFunction:
    """Decorator to check if the colors passed to a function are valid hexadecimal
    codes.

    :param func: The function to be called if the value is valid
    """

    def inner(*args: str, **kwargs):
        for arg in args:
            try:
                if not arg:
                    raise ValueError(func.__name__)
            except ValueError as f:
                print_err(f"Called {f} with empty color", True)

            try:
                HEX(arg)
            except ValueError:
                print_err(f"{arg} is not a valid hex color string", True)

        return func(*args, **kwargs)

    return cast(HexSafeFunction, inner)


@check_hex
def normalize(color: Optional[str]) -> str:
    """Convert ``colp.HEX`` to ``str``.

    This can be used to make al hex representations look the same.

    :param colors: List of colors (only the first is used)
    :returns: Color heaxedecimal normalized in the form of "#000FFF"
    """
    return str(HEX(color))


@check_hex
def make_alt_color(color: Optional[str], inverse: bool = False) -> str:
    """Make a darker color of a lighter one or a lighter one of a darker one

    :param color: Base color
    :param inverse: Invert how this function works
    :returns: Color heaxedecimal normalized in the form of "#000FFF"
    """
    c = HEX(color)
    if not inverse:
        return str(c.darker(1.25) if c.brightness() > 0.5 else c.darker(0.75))
    else:
        return str(c.darker(0.75) if c.brightness() > 0.5 else c.darker(1.25))


@check_hex
def make_orange_from_yellow(color: Optional[str]) -> str:
    """Make a "orange" color from a "yellow" one

    :param color: Yellow color
    :returns: Color heaxedecimal normalized in the form of "#000FFF"
    """
    c = HEX(color)
    return str(c.rotate(-15))


@check_hex
def make_brown_from_orange(color: Optional[str]) -> str:
    """Make a "brown" color from a "orange" one

    :param color: Orange color
    :returns: Color heaxedecimal normalized in the form of "#000FFF"
    """
    c = HEX(color)
    return str(c.rotate(-10).darker(1.1))


@check_hex
def make_average_color(color1: Optional[str], color2: Optional[str]) -> str:
    """Get the average color of two colors

    :param color1: First color
    :param color2: Second color
    :returns: Color heaxedecimal normalized in the form of "#000FFF"
    """
    try:
        a = HEX(color1)
        b = HEX(color2)
    except IndexError:
        print_err("make_average_color requires a list of two items", True)

    return str(
        RGB((a.r + b.r) / 2, (a.g + b.g) / 2, (a.b + b.b) / 2).to(HEX)  # type: ignore
    )
