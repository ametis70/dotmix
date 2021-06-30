import os
import re
from functools import lru_cache
from pathlib import Path
import sys
from typing import Dict, List, Literal, Optional, cast

import click
from colp import Color, HEX
from pydantic import BaseModel

from .utils import load_toml_cfg, load_toml_cfg_model
from .config import get_data_dir

Color.MODE = "css"  # type: ignore
COLORMODE: Literal["terminal", "base16"] = "base16"


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


class Colors(BaseModel):
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
    alt_yellow: str
    alt_orange: str
    alt_green: str
    alt_cyan: str
    alt_blue: str
    alt_brown: str


class ColorschemeTypes(BaseModel):
    terminal: TerminalColorscheme
    base16: Base16Colorscheme


class ColorschemeConfig(BaseModel):
    name: str
    extends: Optional[str]
    custom: Optional[Dict[str, str]]
    colors: ColorschemeTypes


class Colorscheme:
    name: str
    filename: str
    cfg: Optional[ColorschemeConfig]
    colors: Optional[Colors]

    def __init__(self, filename: str, name: str):
        self.name = name
        self.filename = filename
        self.cfg = None
        self.colors = None

    def __repr__(self):
        return f"<Colorscheme {self.name}>"

    def load_cfg(self):
        dir = get_colors_dir()

        cfg = load_toml_cfg_model(dir, self.filename, ColorschemeConfig)
        if cfg:
            self.cfg = cfg
        else:
            click.echo(f"Failed to load {dir / self.filename}", err=True)

    def get_cfg(self):
        if not self.cfg:
            self.load_cfg()

        return self.cfg

    def load_colors(self):
        if not self.cfg:
            self.load_cfg()

        if not self.cfg.extends:
            self.colors = get_colors(self.cfg.colors)

        # extended_colorschemes = get_extended_colorschemes([self])

        return self.colors

    def get_colors(self):
        if not self.colors:
            self.load_colors()

        return self.colors

    def print_colors(self):
        colors = self.get_colors()

        for color, value in colors.dict().items():
            c = cast(HEX, HEX(value))
            r, g, b, = (
                int(c.r * 255),
                int(c.g * 255),
                int(c.b * 255),
            )

            rgb = f"RGB({r : >3}, {g : >3}, {b : >3})"
            click.secho(
                f"  {color : <10} - {str(c) : <7} - {rgb : <20}",
                fg=("white" if c.brightness() < 0.5 else "black"),
                bg=(r, g, b),
            )


def get_colors_dir() -> Path:
    return get_data_dir() / "colors"


def get_colorscheme_files() -> Dict[str, str]:
    colors = {}

    dir = get_colors_dir()
    files = [f for f in os.listdir(dir) if re.match(r".*\.toml", f)]

    for file in files:
        cfg = load_toml_cfg(dir, file)

        if cfg and cfg["name"]:
            colors[cfg["name"]] = file

    return colors


def get_colorschemes() -> Dict[str, Colorscheme]:
    colorschemes: Dict[str, Colorscheme] = {}
    files = get_colorscheme_files()

    for name in files.keys():
        c = get_colorscheme_by_name(name)
        if c:
            colorschemes[name] = c

    return colorschemes


@lru_cache()
def get_colorscheme_by_name(name: str) -> Optional[Colorscheme]:
    files = get_colorscheme_files()

    try:
        filename = files[name]
        return Colorscheme(filename, name)
    except KeyError:
        click.echo(f'Theme "{name}" not found', err=True)


def get_extended_colorschemes(colorschemes: List[Colorscheme]) -> List[Colorscheme]:
    """Get extended colorschemes recursively"""
    colorscheme = colorschemes[-1].get_cfg()

    if not colorscheme.extends:
        return colorschemes

    extended = next(
        (c for c in get_colorschemes().values() if c.name == colorscheme.extends),
        None,
    )

    if extended is None:
        click.secho(
            f"Warning: {colorscheme.name} tried to extend {colorscheme.extends} but it doesn't exists",  # noqa: E501
            err=True,
            fg="yellow",
        )
        return colorschemes

    try:
        if extended in colorschemes:
            raise RecursionError
    except RecursionError:
        click.secho(
            f"{colorscheme.name} tried to extend {colorscheme.extends} but it was extended before",  # noqa: E501
            err=True,
            fg="red",
        )

    colorschemes.append(extended)
    return get_extended_colorschemes(colorschemes)


def make_alt_color(color: Optional[str]) -> str:
    if not color:
        raise ValueError("Error: Called make_alt_color with empty string")

    c = cast(HEX, HEX(color))
    alt_c = c.darker(1.25) if c.brightness() > 0.5 else c.brighter(1.25)
    return str(alt_c)


def make_orange_from_yellow():
    pass


def make_brown_from_orange():
    pass


def get_colors(colors: ColorschemeTypes):
    if COLORMODE == "base16":
        return get_colors_from_base16(colors.base16)

    elif COLORMODE == "terminal":
        raise NotImplementedError

    else:
        raise ValueError('COLORMODE should be "base16" or "terminal"')


def get_colors_from_base16(colors: Base16Colorscheme) -> Colors:
    c = colors

    color_dict = {
        "bg": c.base00,
        "light_bg": c.base01,
        "selection": c.base02,
        "comment": c.base03,
        "dark_fg": c.base04,
        "fg": c.base05,
        "light_fg": c.base06,
        "lighter_fg": c.base07,
        "red": c.base08,
        "orange": c.base09,
        "yellow": c.base0A,
        "green": c.base0B,
        "cyan": c.base0C,
        "blue": c.base0D,
        "magenta": c.base0E,
        "brown": c.base0F,
    }

    try:
        color_dict["alt_red"] = make_alt_color(c.base08)
        color_dict["alt_orange"] = make_alt_color(c.base09)
        color_dict["alt_yellow"] = make_alt_color(c.base0A)
        color_dict["alt_green"] = make_alt_color(c.base0B)
        color_dict["alt_cyan"] = make_alt_color(c.base0C)
        color_dict["alt_blue"] = make_alt_color(c.base0D)
        color_dict["alt_magenta"] = make_alt_color(c.base0E)
        color_dict["alt_brown"] = make_alt_color(c.base0F)
    except ValueError:
        click.secho("Error: Called make_alt_color with empty color", fg="red", err=True)
        sys.exit(1)

    return Colors.parse_obj(color_dict)


# def get_colors_from_terminal_colors(colors: Dict[str, str]) -> Colors
