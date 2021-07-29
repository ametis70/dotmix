from typing import Dict
from dttr.utils import FilesDict, get_all_configs, get_config_by_id, get_config_files
from dttr.config import get_data_dir
from functools import cache, cached_property
from .utils.basiccfg import BasicConfig


class Theme(BasicConfig):
    @cached_property
    def parents(self):
        return self._get_parents(get_themes, [self])


def get_themes_dir():
    return get_data_dir() / "themes"


def get_theme_files() -> FilesDict:
    return get_config_files(get_themes_dir())


def get_themes() -> Dict[str, Theme]:
    return get_all_configs(get_theme_files(), get_theme_by_id)


@cache
def get_theme_by_id(id: str):
    get_config_by_id(id, get_theme_files(), Theme)
