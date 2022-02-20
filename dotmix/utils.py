"""Module for general utilitary functions"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Type, TypeVar, Union, cast

import click
import toml
from pydantic.error_wrappers import ValidationError
from pydantic.main import BaseModel
from toml import TomlDecodeError

VERBOSE = "DOTMIX_VERBOSE"
"""Environment variable name to determine if more information should be printed"""


def get_verbose() -> bool:
    """Get verbosity.

    :return: true if dotmix is running in verbose mode
    """
    return bool(os.getenv(VERBOSE))


def set_verbose(value: bool) -> None:
    """Enable or disable verbosity.

    :param value: True to enable verbosity, false to disable
    """

    if value:
        os.environ[VERBOSE] = "1"
    else:
        if os.getenv(VERBOSE):
            del os.environ[VERBOSE]


def get_path_from_env(env_vars: List[Union[str, Tuple[str, bool]]]) -> str:
    """Get path from enviroment variables

    If no environment variable is set, this function whil call :func:`sys.exit`

    :param env_vars: List that contains strings or tuples with a string and
    a boolean. In both cases, the string is the name of the env var to
    get the path from, while on the tuple the second parameter is used to
    determine if ``/dotmix/`` should be appended to the path of the environment
    variable.

    :returns: The first environment variable that is set.
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
                value += "/dotmix/"
            return value

    print_err(f"Any of the following env vars must be set:\n{print_env_vars()}")
    sys.exit(1)


def load_toml_cfg(path: Path) -> Optional[Dict]:
    """Load a TOML file into a dict

    :param path: Path of the TOML file

    :returns: A dictionary with the parsed values if the file is found
    """
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

    except TomlDecodeError as e:
        print_err(f"Invalid TOML syntax in {path}")
        raise (e)

    finally:
        if fd and not fd.closed:
            fd.close()

    return cfg


BaseModelType = TypeVar("BaseModelType", bound=BaseModel)
"""Models that are submodels of pyantic's ``BaseModel``"""


def load_toml_cfg_model(path: Path, model: Type[BaseModelType]) -> BaseModelType:
    """Generic function to load a TOML file into a dict with :func:`load_toml_cfg` and
        create a model instance.

    :param path: Path of the TOML file to load
    :param model: Model class

    :returns: Instance of the model
    """
    model_instance = None
    cfg = load_toml_cfg(path)
    try:
        model_instance = model.parse_obj(cfg)
    except ValidationError as e:
        print_err(f"invalid/missing values found in {path}\n\n{str(e)}")
        sys.exit(1)

    return model_instance


def deep_merge(dict1: dict, dict2: dict) -> dict:
    """Merges two dictionaries. If keys are conflicting, ``dict2`` is preferred.

    :param dict1: Original dictionary
    :param dict2: Dictionary to be merged (preferred)

    :returns: New dictionary
    """

    def _val(v1, v2):
        if isinstance(v1, dict) and isinstance(v2, dict):
            return deep_merge(v1, v2)
        return v2 or v1

    return {k: _val(dict1.get(k), dict2.get(k)) for k in dict1.keys() | dict2.keys()}


def print_pair(lhs: str, rhs: str):
    """Pretty prints an arbitrary pair of values

    :param lhs: Left hand side
    :param rhs: Right hand side
    """
    click.echo(f"  {click.style(lhs, fg='yellow')} -> {click.style(rhs, fg='green')}")


def print_key_values(dict: Optional[Dict]) -> None:
    """Pretty prints keys and values from dict using :func:`print_pair`

    :param dict: Dictionary to print
    """

    if not dict:
        return

    for key, value in dict.items():
        print_pair(key, value)


def print_err(string: str, exit: bool = False):
    """Print a error and optionaly exit.

    :param string: String to print
    :param exit: If this value is true, the prorgam will exit after printing this
        message
    """
    click.secho(f"Error: {string}", fg="red", err=True)
    if exit:
        sys.exit(1)


def print_wrn(string: str):
    """Print a warning.

    :param string: String to print
    """

    click.secho(f"Warning: {string}", fg="yellow", err=True)


def print_verbose(string: str, **kwargs):
    """Print only if running in verbose mode

    :param string: String to print
    :param **kwargs: Keyword arguments to pass to :func:`click.secho`
    """
    if get_verbose():
        click.secho(string, **kwargs)
