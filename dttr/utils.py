import sys
from os import environ
from pathlib import Path
from typing import List, Optional, Tuple, Type, TypeVar, Union

import toml
from pydantic.error_wrappers import ValidationError
from pydantic.main import BaseModel
from toml import TomlDecodeError


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
            value = environ.get(var[0])
            append = var[1]
        elif type(var) is str:
            value = environ.get(var)

        if value:
            if append:
                value += "/dttr/"
            return value

    print(f"Error: some of the following env vars must be set:\n{print_env_vars()}")
    sys.exit(1)


T = TypeVar("T", bound=BaseModel)


def load_toml_cfg(dir: Path, file: str, model: Type[T]) -> Optional[T]:
    cfg_file = dir / file
    model_instance = None
    fd = None

    try:
        fd = cfg_file.open("r")
        content = fd.read()
        cfg = toml.loads(content)

        if not len(cfg) > 0:
            print(f"Warning: {cfg_file} is empty", file=sys.stderr)

        model_instance = model.parse_obj(cfg)

    except FileNotFoundError:
        print(f"Error: {cfg_file} does no exist", file=sys.stderr)
        raise

    except PermissionError:
        print(
            f"Error: cannot access {cfg_file} due to wrong permissions", file=sys.stderr
        )
        raise

    except ValidationError as e:
        print(
            f"Error: invalid/missing values found in {cfg_file}\n\n{str(e)}",
            file=sys.stderr,
        )
        raise

    except TomlDecodeError:
        print(f"Error: invalid TOML syntax in {cfg_file}", file=sys.stderr)
        raise

    finally:
        if fd and not fd.closed:
            fd.close()

    return model_instance
