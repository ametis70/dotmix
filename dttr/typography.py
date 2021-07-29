from typing import Dict
from dttr.utils import FilesDict, get_all_configs, get_config_by_id, get_config_files
from dttr.config import get_data_dir
from functools import cache, cached_property
from .utils.basiccfg import BasicConfig


class Typography(BasicConfig):
    @cached_property
    def parents(self):
        return self._get_parents(get_typographies, [self])


def get_typographies_dir():
    return get_data_dir() / "themes"


def get_typography_files() -> FilesDict:
    return get_config_files(get_typographies_dir())


def get_typographies() -> Dict[str, Typography]:
    return get_all_configs(get_typography_files(), get_typography_by_id)


@cache
def get_typography_by_id(id: str):
    return get_config_by_id(id, get_typography_files(), Typography)
