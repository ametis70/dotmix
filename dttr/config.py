import os
import sys
from pathlib import Path
from typing import Literal, Optional

import toml
from pydantic import BaseModel

from .utils import get_path_from_env, load_toml_cfg_model, print_err

DefaultSettingType = Literal[
    "colorscheme", "typography", "fileset", "appearance", "pre_hook", "post_hook"
]


class DefaultsConfig(BaseModel):
    appearance: Optional[str]
    typography: Optional[str]
    colorscheme: Optional[str]
    fileset: Optional[str]
    pre_hook: Optional[str]
    post_hook: Optional[str]


class GeneralConfig(BaseModel):
    data_path: str
    out_path: str


class ColorsConfig(BaseModel):
    colormode: Literal["terminal", "base16"]


class Config(BaseModel):
    general: GeneralConfig
    defaults: Optional[DefaultsConfig]
    colors: ColorsConfig


def generate_config(data_path: Path) -> str:
    """Returns a valid dttr TOML config (string)"""

    cfg = Config(
        general={
            "data_path": str(data_path),
            "out_path": str(data_path / "out"),
        },
        colors={"colormode": "base16"},
    )

    return toml.dumps(cfg.dict())


VERBOSE = "DTTR_VERBOSE"


def get_verbose() -> bool:
    return bool(os.getenv(VERBOSE))


def set_verbose(value: bool) -> None:
    if value:
        os.environ[VERBOSE] = "1"
    else:
        if os.getenv(VERBOSE):
            del os.environ[VERBOSE]


def get_data_dir() -> Path:
    """Get dttr data path"""
    env_vars = ["DTTR_DATA_DIR", ("XDG_DATA_HOME", True)]

    return Path(get_path_from_env(env_vars))


def get_config_dir() -> Path:
    """Get dttr config path"""
    env_vars = ["DTTR_CONFIG_DIR", ("XDG_CONFIG_HOME", True)]

    return Path(get_path_from_env(env_vars))


def get_config() -> Config:
    config_path = get_config_dir()
    cfg = load_toml_cfg_model(config_path / "config.toml", Config)

    if cfg:
        return cfg

    else:
        print_err("Couldn't find config file")
        sys.exit(1)


def get_default_setting(type: DefaultSettingType) -> Optional[str]:
    v: Optional[str] = None
    try:
        v = get_config().defaults.dict()[type]
    except KeyError:
        pass
    finally:
        return v


def create_config(
    config_path: Optional[Path] = None,
    data_path: Optional[Path] = None,
    force: bool = False,
) -> None:
    """Create the config file if it doesn't exist

    This function takes to optional parameters to change the configuration directory and
    data directory, but they are just for testing purposes. To change those values when
    when using the CLI, modify the DTTR_CONFIG_DIR and DTTR_DATA_DIR environment
    variables
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

    dirs = ["templates", "templates/base", "colors", "fonts", "themes"]

    for dir in dirs:
        p = path / dir
        p.mkdir()
