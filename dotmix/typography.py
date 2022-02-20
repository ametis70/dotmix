"""Data module for typographies"""

from functools import cache, cached_property
from typing import Dict, Optional

from dotmix.config import get_data_dir
from dotmix.data import (
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
    """Get typographies directory.

    :returns: Appearances data files directory
    """

    return get_data_dir() / "typographies"


def get_typography_files() -> DataFilesDict:
    """Get typography data files.

    :returns: Appearance files dictionary
    """

    return get_data_files(get_typographies_dir())


def get_typographies() -> Dict[str, Typography]:
    """Get all typography instances.

    :returns: Dict of typography instances
    """

    return get_all_data_instances(get_typography_files(), get_typography_by_id)


@cache
def get_typography_by_id(id: str) -> Optional[Typography]:
    """Get a specific typography instance by id.

    :param id: Id of the typography to get
    :returns: Typography instance
    """

    return get_data_by_id(id, get_typography_files(), Typography)
