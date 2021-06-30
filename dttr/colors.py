import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, cast

import click
from colp import Color, HEX
from pydantic import BaseModel

from .utils import load_toml_cfg, load_toml_cfg_model
from .config import get_data_dir

Color.MODE = "css"  # type: ignore


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
    terminal: Optional[TerminalColorscheme]
    base16: Optional[Base16Colorscheme]


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

    def __repr__(self):
        return f"<Colorscheme {self.name}>"

    def load(self):
        dir = get_colors_dir()

        cfg = load_toml_cfg_model(dir, self.filename, ColorschemeConfig)
        if cfg:
            self.cfg = cfg
        else:
            click.echo(f"Failed to load {dir / self.filename}", err=True)

    def get_cfg(self):
        if not self.cfg:
            self.load()

        return self.cfg

    def get_colors(self):
        if not self.cfg:
            self.load()

        # if not self.cfg.extends:

        # extended_templates = get_extended_colorschemes([self])


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


def make_alt_color(color: str) -> str:
    c = cast(HEX, HEX(color))
    alt_c = c.darker(1.25) if c.brightness() > 0.5 else c.brighter(1.25)
    return str(alt_c)


def make_orange_from_yellow():
    pass


def make_brown_from_orange():
    pass


def get_colors_from_base16(colors: Dict[str, str]) -> Colors:
    c = colors

    colors = {
        "bg": c["base00"],
        "light_bg": c["base01"],
        "selection": c["base02"],
        "comment": c["base03"],
        "dark_fg": c["base04"],
        "fg": c["base05"],
        "light_fg": c["base06"],
        "lighter_fg": c["base07"],
        "red": c["base08"],
        "orange": c["base09"],
        "yellow": c["base0A"],
        "green": c["base0B"],
        "cyan": c["base0C"],
        "blue": c["base0D"],
        "magenta": c["base0E"],
        "brown": c["base0F"],
    }

    colors["alt_red"] = make_alt_color(c["base08"])
    colors["alt_orange"] = make_alt_color(c["base09"])
    colors["alt_yellow"] = make_alt_color(c["base0A"])
    colors["alt_green"] = make_alt_color(c["base0B"])
    colors["alt_cyan"] = make_alt_color(c["base0C"])
    colors["alt_blue"] = make_alt_color(c["base0D"])
    colors["alt_magenta"] = make_alt_color(c["base0E"])
    colors["alt_brown"] = make_alt_color(c["base0F"])

    return Colors.parse_obj(colors)
