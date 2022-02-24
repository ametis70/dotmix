"""Module for reading and writing the configuration"""


import sys
from pathlib import Path
from typing import Literal, Optional

import toml
from pydantic import BaseModel

from dotmix.utils import get_path_from_env, load_toml_cfg_model, print_err

# Types:

ThemeKeys = Literal[
    "colorscheme", "typography", "fileset", "appearance", "pre_hook", "post_hook"
]
"""Possible keys for ``dotmix.config.ThemeConfig``"""


# Models:


class ThemeConfig(BaseModel):
    """Model for specifying a theme (dictionary of IDs)

    All keys are optional and they take an ID (string) as a value

    :param appearance: Appearance ID
    :param typography: Typography ID
    :param colorscheme: Colorscheme ID
    :param fileset: Fileset ID
    :param pre_hook: Pre hook ID
    :param post_hook: Post hook ID

    """

    appearance: Optional[str]
    typography: Optional[str]
    colorscheme: Optional[str]
    fileset: Optional[str]
    pre_hook: Optional[str]
    post_hook: Optional[str]


class GeneralConfig(BaseModel):
    """General configuration

    :param data_path: Path for the data directory
    :param out_path: Path for the output files

    """

    data_path: str
    out_path: str


class ColorsConfig(BaseModel):
    """Colors configuration

    :param colormode: Default colormode ("terminal" or "base16")

    """

    colormode: Literal["terminal", "base16"]


class Config(BaseModel):
    """Root config model. This only holds other models for organizative purposes"""

    general: GeneralConfig
    defaults: Optional[ThemeConfig]
    current: Optional[ThemeConfig]
    colors: ColorsConfig


# Functions:


def generate_config(data_path: Path) -> str:
    """Generate the default configuration.

    :return: Returns a valid dotmix TOML config"""

    cfg = Config(
        general={
            "data_path": str(data_path),
            "out_path": str(data_path / "out"),
        },
        colors={"colormode": "base16"},
    )

    return toml.dumps(cfg.dict())


def get_data_dir() -> Path:
    """Get the data directory's path, where all data files, hooks and output files are
    stored.

    By default, the path is is ``$XDG_DATA_HOME/dotmix``, but it can be modified by
    setting the environemt variable ``$DOTMIX_DATA_DIR``.

    :return: Data path
    """
    env_vars = ["DOTMIX_DATA_DIR", ("XDG_DATA_HOME", True)]

    return Path(get_path_from_env(env_vars))


def get_config_dir() -> Path:
    """Get the configuration directory's path, where the configuration is stored.

    By default, the path is is ``$XDG_CONFIG_HOME/dotmix``, but it can be modified by
    setting the environemt variable ``$DOTMIX_CONFIG_DIR``.

    :return: Config path"""

    env_vars = ["DOTMIX_CONFIG_DIR", ("XDG_CONFIG_HOME", True)]

    return Path(get_path_from_env(env_vars))


def get_config() -> Config:
    """Reads the configuration file and returns a :class:`dotmix.config.Config` instance

    :returns: Parsed configuration model instance
    """
    config_path = get_config_dir()
    cfg = load_toml_cfg_model(config_path / "config.toml", Config)

    if cfg:
        return cfg

    else:
        print_err("Couldn't find config file")
        sys.exit(1)


def set_config(cfg: Config):
    config_path = get_config_dir() / "config.toml"

    with config_path.open("w") as f:
        f.writelines(toml.dumps(cfg.dict()))


def get_default_setting(type: ThemeKeys) -> Optional[str]:
    """Get value from key in :class:`dotmix.config.Config.defaults` if defined.

    :return: String with the value associated with the key if it exists
    """
    v: Optional[str] = None
    try:
        defaults = get_config().defaults
        if defaults is None:
            print_err("Default settings not found")
            return

        v = defaults.dict()[type]

    except KeyError:
        pass
    finally:
        return v


def get_current_theme() -> Optional[ThemeConfig]:
    """Get the current applied theme from :attr:`dotmix.config.Config.theme`

    :return: current applied theme
    """

    return get_config().current


def set_current_theme(
    appearance: Optional[str],
    typography: Optional[str],
    colorscheme: Optional[str],
    fileset: Optional[str],
    pre_hook: Optional[str],
    post_hook: Optional[str],
):
    cfg = get_config()
    cfg.current = ThemeConfig(
        appearance=appearance,
        typography=typography,
        colorscheme=colorscheme,
        fileset=fileset,
        pre_hook=pre_hook,
        post_hook=post_hook,
    )
    set_config(cfg)


def create_config(
    config_path: Optional[Path] = None,
    data_path: Optional[Path] = None,
    force: bool = False,
) -> None:
    """Create the config file if it doesn't exist

    This function takes to optional parameters to change the configuration directory and
    data directory, but they are just for testing purposes. To change those values when
    when using the CLI, modify the ``$DOTMIX_CONFIG_DIR`` and ``$DOTMIX_DATA_DIR``
    environment variables

    :param config_path: override the config path returned
        by :func:`dotmix.Config.get_config_dir`
    """

    if not config_path:
        config_path = get_config_dir()

    if not config_path.exists() and not config_path.is_dir():
        config_path.mkdir()

    filename = "config.toml"
    config_file = config_path / filename

    if not force and config_file.exists():
        print_err(f"Error: {filename} exists")
        return

    if not data_path:
        data_path = get_data_dir()

    with config_file.open("w", encoding="utf-8") as f:
        config = generate_config(data_path)
        if config:
            f.write(config)


def scaffold_data_path() -> None:
    """Create the directory structure for the data path"""
    path = Path(get_config().general.data_path)

    if not path.is_dir():
        path.mkdir()

    if len(list(path.iterdir())) > 0:
        print("Skipping, directory not empty")
        return

    dirs = ["filesets", "filesets/base", "colorschemes", "typographies", "appearances"]

    for dir in dirs:
        p = path / dir
        p.mkdir()
