import sys
import toml
from dttr.utils import get_path_from_env
from pathlib import Path
from typing import Optional, TypedDict, cast


class GeneralConfig(TypedDict):
    data_path: str
    out_path: str


class DefaultsConfig(TypedDict, total=False):
    template: str
    theme: str
    colors: str
    fonts: str


class HooksConfig(TypedDict, total=False):
    pre: str
    post: str


class Config(TypedDict, total=False):
    general: GeneralConfig
    defaults: DefaultsConfig
    hooks: HooksConfig


def generate_config(data_path: Path) -> str:
    """Returns a valid dttr TOML config (string)"""

    cfg: Config = {
        "general": {
            "data_path": str(data_path),
            "out_path": str(data_path / "out"),
        },
    }

    return toml.dumps(cfg)


def get_data_path() -> Path:
    """Get dttr data path"""
    env_vars = ["DTTR_DATA_DIR", ("XDG_DATA_HOME", True)]

    return Path(get_path_from_env(env_vars))


def get_config_path() -> Path:
    """Get dttr config path"""
    env_vars = ["DTTR_CONFIG_DIR", ("XDG_CONFIG_HOME", True)]

    return Path(get_path_from_env(env_vars))


def get_config() -> Config:
    config_path = get_config_path()
    config_file = config_path / "config.toml"
    if config_file.exists:
        return cast(Config, toml.load(config_file))
    else:
        print("Error: {config_file} doesn't exist")
        sys.exit(1)


def create_config(config_path: Optional[Path] = None, data_path: Optional[Path] = None):
    """Create the config file if it doesn't exist

    This function takes to optional parameters to change the configuration directory and
    data directory, but they are just for testing purposes. To change those values when
    when using the CLI, modify the DTTR_CONFIG_DIR and DTTR_DATA_DIR environment
    variables
    """

    if not config_path:
        config_path = get_config_path()

    if not config_path.exists() and not config_path.is_dir():
        config_path.mkdir()

    filename = "config.toml"
    config_file = config_path / filename

    if config_file.exists():
        print(f"Error: {filename} exists")
        return

    if not data_path:
        data_path = get_data_path()

    with config_file.open("w", encoding="utf-8") as f:
        config = generate_config(data_path)
        if config:
            f.write(config)


def scaffold_data_path() -> None:
    """Create the directory structure for the data path"""
    path = Path(get_config().get("general").get("data_path"))

    if not path.is_dir():
        path.mkdir()

    if len(list(path.iterdir())) > 0:
        print("Skipping, directory not empty")
        return

    dirs = ["templates", "templates/base", "colors", "fonts", "themes"]

    for dir in dirs:
        p = path / dir
        p.mkdir()
