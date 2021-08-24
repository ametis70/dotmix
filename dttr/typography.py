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


class Typography(BasicData):
    @cached_property
    def parents(self):
        return self._get_parents(get_typographies, [self])


def get_typographies_dir():
    return get_data_dir() / "themes"


def get_typography_files() -> DataFilesDict:
    return get_data_files(get_typographies_dir())


def get_typographies() -> Dict[str, Typography]:
    return get_all_data_instances(get_typography_files(), get_typography_by_id)


@cache
def get_typography_by_id(id: str) -> Optional[Typography]:
    return get_data_by_id(id, get_typography_files(), Typography)
