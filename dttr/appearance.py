from functools import cache, cached_property
from typing import Dict, Optional

from dttr.config import get_data_dir
from dttr.data import (
    BasicData,
    DataFilesDict,
    get_all_data_instances,
    get_data_by_id,
    get_data_files,
)


class Appearance(BasicData):
    @cached_property
    def parents(self):
        return self._get_parents(get_appearances, [self])


def get_appearances_dir():
    return get_data_dir() / "themes"


def get_appearance_files() -> DataFilesDict:
    return get_data_files(get_appearances_dir())


def get_appearances() -> Dict[str, Appearance]:
    return get_all_data_instances(get_appearance_files(), get_appearance_by_id)


@cache
def get_appearance_by_id(id: str) -> Optional[Appearance]:
    return get_data_by_id(id, get_appearance_files(), Appearance)
