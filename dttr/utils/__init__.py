import os
import re
import sys
from functools import cache
from pathlib import Path
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypedDict,
    TypeVar,
    Union,
    cast,
)

import click
import toml
from pydantic.error_wrappers import ValidationError
from pydantic.main import BaseModel
from toml import TomlDecodeError

from dttr.config import get_verbose
from dttr.utils.abstractcfg import AbstractConfigType


def get_path_from_env(env_vars: List[Union[str, Tuple[str, bool]]]) -> str:
    """Return the first variable that is set in env_vars

    env_vars is a list that contains strings or tuples with a string and
    a boolean. In both cases, the string is the name of the env var to
    get the path from, while on the tuple the second parameter is used to
    determine if '/dttr/' should be appended to the path of the environment
    variable.
    """

    def print_env_vars() -> str:
        """Return only the name for the variables in env_vars"""
        vars = []
        for var in env_vars:
            val = None
            if type(var) is tuple:
                val = var[0]
            elif type(var) is str:
                val = var
            if val:
                vars.append(val)

        return "\n".join(vars)

    for var in env_vars:
        value = None
        append = False
        if type(var) is tuple:
            value = os.environ.get(var[0])
            append = var[1]
        elif type(var) is str:
            value = os.environ.get(var)

        if value:
            if append:
                value += "/dttr/"
            return value

    print_err(f"Any of the following env vars must be set:\n{print_env_vars()}")
    sys.exit(1)


def load_toml_cfg(path: Path) -> Optional[Dict]:
    fd = None
    cfg = None

    try:
        fd = path.open("r")
        content = fd.read()
        cfg = cast(Dict, toml.loads(content))

        if not cfg:
            print_wrn(f"{path} exist but it's empty")

    except FileNotFoundError:
        print_err(f"{path} does not exist", True)

    except PermissionError:
        print_err(f"Cannot access {path} due to wrong permissions", True)

    except TomlDecodeError:
        print_err(f"Invalid TOML syntax in {path}", True)

    finally:
        if fd and not fd.closed:
            fd.close()

    return cfg


T = TypeVar("T", bound=BaseModel)


def load_toml_cfg_model(path: Path, model: Type[T]) -> T:
    model_instance = None
    cfg = load_toml_cfg(path)
    try:
        model_instance = model.parse_obj(cfg)
    except ValidationError as e:
        print_err(f"invalid/missing values found in {path}\n\n{str(e)}")
        sys.exit(1)

    return model_instance


def deep_merge(dict1: dict, dict2: dict) -> dict:
    """Merges two dicts. If keys are conflicting, dict2 is preferred."""

    def _val(v1, v2):
        if isinstance(v1, dict) and isinstance(v2, dict):
            return deep_merge(v1, v2)
        return v2 or v1

    return {k: _val(dict1.get(k), dict2.get(k)) for k in dict1.keys() | dict2.keys()}


class SettingsMetadata(TypedDict):
    id: str
    name: str
    path: Path


SettingsDict = Dict[str, SettingsMetadata]


@cache
def get_config_files(dir: Path):
    files_dict: SettingsDict = {}

    files = [f for f in os.listdir(dir) if re.match(r".*\.toml", f)]

    for file in files:
        path = Path(dir / file)

        cfg = load_toml_cfg(Path(dir / file))
        name = cfg["name"]
        id = path.with_suffix("").name

        if cfg and name:
            files_dict[id] = {"id": id, "path": path, "name": name}

    return files_dict


GenericSettingsGetter = Callable[[str], Optional[AbstractConfigType]]


def get_config_by_id(
    id: str, files: SettingsDict, cls: Type[AbstractConfigType]
) -> Optional[AbstractConfigType]:
    try:
        file = files[id]
        id = file["id"]
        name = file["name"]
        path = file["path"]
        return cls(id, name, path)
    except KeyError:
        print_err(f'{cls.__name__} "{id}" not found')


def get_all_configs(
    files: SettingsDict, getter: GenericSettingsGetter[AbstractConfigType]
) -> Dict[str, AbstractConfigType]:
    cfgs: Dict[str, AbstractConfigType] = {}

    for name in files.keys():
        c = getter(name)
        if c:
            cfgs[name] = c

    return cfgs


def print_pair(lhs: str, rhs: str):
    click.echo(f"  {click.style(lhs, fg='yellow')} -> {click.style(rhs, fg='green')}")


def print_key_values(dict: Optional[Dict]) -> None:
    if not dict:
        return

    for key, value in dict.items():
        print_pair(key, value)


def print_err(string: str, exit: bool = False):
    click.secho(f"Error: {string}", fg="red", err=True)
    if exit:
        sys.exit(1)


def print_wrn(string: str):
    click.secho(f"Warning: {string}", fg="warning", err=True)


def print_verbose(string: str, **kwargs):
    if get_verbose():
        click.secho(string, **kwargs)
