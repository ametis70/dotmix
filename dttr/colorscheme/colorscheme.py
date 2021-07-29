import os
from functools import cache, cached_property
from pathlib import Path
from typing import Dict, Literal, Optional, cast

import click
from .colp import HEX

from .utils import (
    make_alt_color,
    make_alt_color_inverse,
    make_average_color,
    make_brown_from_orange,
    make_orange_from_yellow,
)

from dttr.utils import (
    FilesDict,
    deep_merge,
    get_all_configs,
    get_config_by_id,
    get_config_files,
    load_toml_cfg_model,
)
from dttr.utils.abstractcfg import BaseSchema, AbstractConfig
from dttr.config import get_config, get_data_dir

from .models import (
    ParsedColorschemes,
    DttrColorscheme,
    TerminalColorscheme,
    Base16Colorscheme,
)

COLORMODE: Literal["terminal", "base16"] = "terminal"


class ColorschemeConfig(BaseSchema):
    colors: ParsedColorschemes


class Colorscheme(AbstractConfig[ColorschemeConfig, DttrColorscheme]):
    def load_cfg(self):
        self._cfg = load_toml_cfg_model(self.cfg_file, ColorschemeConfig)

    def compute_data(self):
        if not self.cfg.extends:
            self._data = compute_colors(self.cfg.colors)

        colors_dict = {}
        for colorscheme in reversed(self.parents):
            colors_dict = deep_merge(colors_dict, colorscheme.cfg.colors.dict())

        self._data = compute_colors(ParsedColorschemes.parse_obj(colors_dict))

    @cached_property
    def parents(self):
        return self._get_parents(get_colorschemes, [self])

    def print_data(self):
        colors = self.data

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


def get_colorschemes_dir() -> Path:
    return get_data_dir() / "colors"


def get_colorscheme_files() -> FilesDict:
    return get_config_files(get_colorschemes_dir())


def get_colorschemes() -> Dict[str, Colorscheme]:
    return get_all_configs(get_colorscheme_files(), get_colorscheme_by_id)


@cache
def get_colorscheme_by_id(id: str) -> Optional[Colorscheme]:
    return get_config_by_id(id, get_colorscheme_files(), Colorscheme)


def compute_colors(colors: ParsedColorschemes):
    colormode = Optional[Literal["terminal", "base16"]]
    env = os.getenv("DTTR_COLORMODE")
    if env == "terminal" or env == "base16":
        colormode = env
    else:
        colormode = get_config().colors.colormode

    if colormode == "base16":
        return compute_colorscheme_from_base16(colors.base16)

    elif colormode == "terminal":
        return compute_colorscheme_from_terminal(colors.terminal)

    else:
        raise ValueError('colormode should be "base16" or "terminal"')


def compute_colorscheme_from_base16(
    colors: Base16Colorscheme,
) -> DttrColorscheme:
    c = colors

    color_dict = {
        "bg": c.base00,
        "light_bg": c.base01,
        "selection": c.base02,
        "comment": c.base03,
        "dark_fg": c.base04,
        "fg": c.base05,
        "light_fg": c.base06,
        "lighter_bg": c.base07,
        "red": c.base08,
        "orange": c.base09,
        "yellow": c.base0A,
        "green": c.base0B,
        "cyan": c.base0C,
        "blue": c.base0D,
        "magenta": c.base0E,
        "brown": c.base0F,
    }

    color_dict["alt_red"] = make_alt_color(c.base08)
    color_dict["alt_orange"] = make_alt_color(c.base09)
    color_dict["alt_yellow"] = make_alt_color(c.base0A)
    color_dict["alt_green"] = make_alt_color(c.base0B)
    color_dict["alt_cyan"] = make_alt_color(c.base0C)
    color_dict["alt_blue"] = make_alt_color(c.base0D)
    color_dict["alt_magenta"] = make_alt_color(c.base0E)
    color_dict["alt_brown"] = make_alt_color(c.base0F)

    return DttrColorscheme.parse_obj(color_dict)


def compute_colorscheme_from_terminal(
    colors: TerminalColorscheme,
) -> DttrColorscheme:
    c = colors

    color_dict = {
        "bg": c.bg,
        "light_bg": c.color8,
        "comment": c.color0,
        "dark_fg": c.color7,
        "fg": c.fg,
        "light_fg": c.color15,
        "red": c.color1,
        "green": c.color2,
        "yellow": c.color3,
        "blue": c.color4,
        "magenta": c.color5,
        "cyan": c.color6,
        "alt_red": c.color9,
        "alt_green": c.color10,
        "alt_yellow": c.color11,
        "alt_blue": c.color12,
        "alt_magenta": c.color13,
        "alt_cyan": c.color14,
    }

    color_dict["orange"] = make_orange_from_yellow(color_dict["yellow"])
    color_dict["brown"] = make_brown_from_orange(color_dict["orange"])
    color_dict["alt_orange"] = make_alt_color(color_dict["orange"])
    color_dict["alt_brown"] = make_alt_color(color_dict["brown"])
    color_dict["selection"] = make_average_color(
        color_dict["light_bg"], color_dict["comment"]
    )
    color_dict["lighter_bg"] = make_alt_color_inverse(color_dict["light_fg"])

    return DttrColorscheme.parse_obj(color_dict)