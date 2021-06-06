import sys
from os import environ
from typing import List, Tuple, Union


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
