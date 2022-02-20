"""Data module for appearances"""

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


class Appearance(BasicData):
    """Data class for appearances"""

    @cached_property
    def parents(self):
        return self._get_parents(get_appearances, [self])


def get_appearances_dir():
    """Get appearances directory.

    :returns: Appearances data files directory
    """

    return get_data_dir() / "appearances"


def get_appearance_files() -> DataFilesDict:
    """Get appearance data files.

    :returns: Appearance files dictionary
    """

    return get_data_files(get_appearances_dir())


def get_appearances() -> Dict[str, Appearance]:
    """Get all appearance instances.

    :returns: Dict of appearance instances
    """

    return get_all_data_instances(get_appearance_files(), get_appearance_by_id)


@cache
def get_appearance_by_id(id: str) -> Optional[Appearance]:
    """Get a specific appearance instance by id.

    :param id: Id of the appearance to get
    :returns: Appearance instance
    """

    return get_data_by_id(id, get_appearance_files(), Appearance)
