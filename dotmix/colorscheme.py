"""Data module for colorschemes"""
import os
from functools import cache, cached_property
from pathlib import Path
from typing import Any, Dict, Literal, Optional, TypedDict, cast

import click

from dotmix.colorutils import (
    Base16Colorscheme,
    DotmixColorscheme,
    ParsedColorschemes,
    TerminalColorscheme,
    make_alt_color,
    make_average_color,
    make_brown_from_orange,
    make_orange_from_yellow,
    normalize,
)
from dotmix.config import get_config, get_data_dir
from dotmix.data import (
    AbstractData,
    DataFileModel,
    DataFilesDict,
    get_all_data_instances,
    get_data_by_id,
    get_data_files,
)
from dotmix.utils import deep_merge, load_toml_cfg_model, print_key_values
from dotmix.vendor.colp import HEX


class ColorschemeDataFileModel(DataFileModel):
    """Data file model for colorschemes"""

    colors: ParsedColorschemes


class ColorschemeData(TypedDict):
    """Computed data type for colorscheme"""

    colors: DotmixColorscheme
    custom: Dict[str, Any]


class Colorscheme(AbstractData[ColorschemeDataFileModel, ColorschemeData]):
    """Data class for appearances"""

    def load_data_file(self):
        self.file_data = load_toml_cfg_model(
            self.data_file_path, ColorschemeDataFileModel
        )

    def compute_data(self):
        if not self.file_data.extends:
            self.data: ColorschemeData = {
                "colors": compute_colors(self.file_data.colors),
                "custom": self.file_data.custom or {},
            }

        colors_dict = {}
        custom_dict = {}
        for colorscheme in reversed(self.parents):
            colors_dict = deep_merge(colors_dict, colorscheme.file_data.colors.dict())
            custom_dict = deep_merge(custom_dict, colorscheme.file_data.custom)

        self.data = {
            "colors": compute_colors(ParsedColorschemes.parse_obj(colors_dict)),
            "custom": custom_dict,
        }

    @cached_property
    def parents(self):
        return self._get_parents(get_colorschemes, [self])

    def print_data(self):
        colors = self.data["colors"]

        click.secho(f"Colors from {self.name}\n", fg="blue", bold=True)
        for color, value in colors.dict().items():
            c = cast(HEX, HEX(value))
            r, g, b, = (
                int(c.r * 255),
                int(c.g * 255),
                int(c.b * 255),
            )

            rgb = f"RGB({r : >3}, {g : >3}, {b : >3})"
            click.echo(
                "  "
                + click.style(
                    f"  {color : <11} - {str(c) : <7} - {rgb : <20}",
                    fg=("white" if c.brightness() < 0.5 else "black"),
                    bg=(r, g, b),
                )
            )

        custom = self.data["custom"]
        if len(custom) == 0:
            return

        click.secho(f"\nCustom variables from {self.name}\n", fg="blue", bold=True)
        print_key_values(custom)


def get_colorschemes_dir() -> Path:
    """Get colorscheme directory.

    :returns: Colorscheme data files directory
    """
    return get_data_dir() / "colorschemes"


def get_colorscheme_files() -> DataFilesDict:
    """Get colorscheme files.

    :returns: Colorscheme data files dictionary
    """

    return get_data_files(get_colorschemes_dir())


def get_colorschemes() -> Dict[str, Colorscheme]:
    """Get all colorscheme instances.

    :returns: Dict of colorscheme instances
    """

    return get_all_data_instances(get_colorscheme_files(), get_colorscheme_by_id)


@cache
def get_colorscheme_by_id(id: str) -> Optional[Colorscheme]:
    """Get a specific colorscheme instance by id.

    :param id: Id of the colorscheme to get
    :returns: Colorscheme instance
    """

    return get_data_by_id(id, get_colorscheme_files(), Colorscheme)


def compute_colors(colors: ParsedColorschemes) -> DotmixColorscheme:
    """Function called by :meth:`dotmix.colorscheme.Colorscheme.compute_data` to generate
    a colorscheme that can be used by the template engine

    Read the enviorment variable ``DOTMIX_COLORMODE`` to determine what function to call
    based on the colormode. If the variable is not set, it will fall back to reading
    the configuration file.

    :param colors: Parsed colorschemes model instance
    :returns: Ready to use colorscheme
    """
    colormode = Optional[Literal["terminal", "base16"]]
    env = os.getenv("DOTMIX_COLORMODE")
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
) -> DotmixColorscheme:
    """Generate a dotmix colorscheme from a base16 colorscheme model instance.

    :param colors: Instance of parsed base16 colorscheme model
    :returns: Ready to use colorscheme
    """
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

    color_dict = {k: normalize(v) for k, v in color_dict.items()}

    color_dict["alt_red"] = make_alt_color(c.base08)
    color_dict["alt_orange"] = make_alt_color(c.base09)
    color_dict["alt_yellow"] = make_alt_color(c.base0A)
    color_dict["alt_green"] = make_alt_color(c.base0B)
    color_dict["alt_cyan"] = make_alt_color(c.base0C)
    color_dict["alt_blue"] = make_alt_color(c.base0D)
    color_dict["alt_magenta"] = make_alt_color(c.base0E)
    color_dict["alt_brown"] = make_alt_color(c.base0F)

    return DotmixColorscheme.parse_obj(color_dict)


def compute_colorscheme_from_terminal(
    colors: TerminalColorscheme,
) -> DotmixColorscheme:
    """Generate a dotmix colorscheme from a terminal colorscheme model instance.

    :param colors: Instance of parsed terminal colorscheme model
    :retunrs: Ready to use colorscheme
    """

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

    color_dict = {k: normalize(v) for k, v in color_dict.items()}

    color_dict["orange"] = make_orange_from_yellow(color_dict["yellow"])
    color_dict["brown"] = make_brown_from_orange(color_dict["orange"])
    color_dict["alt_orange"] = make_alt_color(color_dict["orange"])
    color_dict["alt_brown"] = make_alt_color(color_dict["brown"])
    color_dict["selection"] = make_average_color(
        color_dict["light_bg"], color_dict["comment"]
    )
    color_dict["lighter_fg"] = make_alt_color(color_dict["light_fg"], inverse=True)

    return DotmixColorscheme.parse_obj(color_dict)
