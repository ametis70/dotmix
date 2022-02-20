"""Base data module.

This module contains all abstract classes, typings and functions that the concrete
data modules are built upon.
"""

import os
import re
from abc import ABCMeta, abstractmethod
from functools import cache, cached_property
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypedDict,
    TypeVar,
    Union,
    cast,
)

from pydantic import BaseModel

from dotmix.utils import (
    deep_merge,
    load_toml_cfg,
    load_toml_cfg_model,
    print_err,
    print_key_values,
    print_wrn,
)

# Types:

DataClassType = TypeVar("DataClassType", bound="AbstractData")
"""Type for classes that extend :class:`dotmix.data.AbstractData`"""

DataFileModelType = TypeVar("DataFileModelType", bound="DataFileModel")
"""Type for models that are submodels of :class:`dotmix.data.DataFileModel``"""

DataType = TypeVar("DataType", bound=Union[TypedDict, BaseModel, Dict])
"""This type represent which values the computed data for
:class:`dotmix.data.AbstractData` can take"""


GenericDataGetter = Callable[[str], Optional[DataClassType]]
"""Callable typing for functions that return instances of subclasses
of :class:`dotmix.data.AbstractData`"""


CustomDictTypes = Union[str, bool, int, List, Dict]
"""Types for the custom dict of :class:`dotmix.data.DataFileModel`"""


class DataFileMetadata(TypedDict):
    """Typing for the dictionary that is returned by
    :func:`dotmix.data.get_config_files`"""

    id: str
    name: str
    path: Path


DataFilesDict = Dict[str, DataFileMetadata]
"""Dictionary of :class:`dotmix.data.DataFileMetadata`"""


# Models:


class DataFileModel(BaseModel):
    """Base model for data files.

    All instances of data classes are created from a file
    that are validated against this model

    :param name: Name of the data instance (this is only for repsentational purposes)
        and it's not the same as the data ID
    :param extends: Optional ID of data another data file from the same category (class)
        as this instance
    :param custom: A dictionary that contains actual data and may be used in different
        ways by the data class
    """

    name: str
    extends: Optional[str]
    custom: Optional[Dict[str, CustomDictTypes]]


# Classes:


class AbstractData(Generic[DataFileModelType, DataType], metaclass=ABCMeta):
    """Abstract Data base class.

    All data classes are subclasses of this.

    :param id: Unique ID of the data instance. The ID is only unique to a specific
        subclass (can be reused in different subclasses)
    :param name: Name for repsentational purposes
    :param data_file_path: Path of the data file
    """

    id: str
    name: str
    data_file_path: Path
    _computed_data: Optional[DataType]
    _file_data: Optional[DataFileModelType]
    _parents: Optional[List[BaseModel]]

    def __init__(self, id: str, name: str, data_file_path: Path):
        self.id = id
        self.name = name
        self.data_file_path = data_file_path

        self._file_data = None
        self._computed_data = None
        self._parents = None

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}>"

    @abstractmethod
    def load_data_file() -> None:
        """This method loads (parses and validate) the data file for this instance (see
        :attr:`dotmix.data.AbstractData.data_file_path`)"""
        pass

    @property
    def file_data(self) -> Optional[DataFileModelType]:
        """Get the parsed file data model instance. If it is not loaded yet, this
            function will call :meth:`dotmix.data.AbstractData.load_data_file` first

        :returns: Loaded data from instance data file
        """
        if not self._file_data:
            self.load_data_file()

        return self._file_data

    @file_data.setter
    def file_data(self, value: DataFileModelType) -> None:
        """Setter for ``file_data``. This setter is meant to be used by
        :meth:`dotmix.data.AbstractData.load_data_file`"""
        self._file_data = value

    @property
    def data(self) -> DataType:
        """This property holds the "computed data" for this instance.

        This is the data that should be fed to the template processing library.

        The computed data holds different values depending on the sublcass (for
        instance, the file paths for a fileset or the hexadecimal codes for a
        colorscheme), and if the data class instance extends another instance, it will
        probably have inherited values from that instances too.

        If the data is not computed yet, this will call
        :meth:`dotmix.data.AbstractData.compute_data` first
        """

        if not self._computed_data:
            self.compute_data()

        return cast(DataType, self._computed_data)

    @data.setter
    def data(self, value: DataType) -> None:
        """Setter for ``data``. This setter is meant to be used by
        :meth:`dotmix.data.AbstractData.compute_data`"""

        self._computed_data = value

    @abstractmethod
    def compute_data(self) -> None:
        """This method should be implemented by subclasses to populate
        :attr:`dotmix.data.AbstractData.data` property with the values that subclass
        expects"""
        pass

    @abstractmethod
    def print_data() -> None:
        """Pretty prints the data property from this instance"""
        pass

    @cached_property
    @abstractmethod
    def parents(self) -> List[DataClassType]:
        """This method uses :meth:`dotmix.data.AbstractData._get_parents` to get parents
        recursively.

        :returns: List with this instance on the first index followed by its parents
            (if there are any)
        """
        pass

    @classmethod
    def _get_parents(
        cls: Type[DataClassType],
        get_all_instances: Callable[[], Dict[str, DataClassType]],
        configs: List[DataClassType],
    ) -> List[DataClassType]:
        """Class method that tecursively populates and returns a list with the class
        instance and all parents (extended) instances

        This is meant to be called in :attr:`dotmix.data.AbstractData.parents` with a
        ``get_all_instances`` function that returns the config files that can be
        used with this particular subclass
        """
        last_cfg = configs[-1].file_data

        if not last_cfg.extends:
            return configs

        parent = next(
            (c for c in get_all_instances().values() if c.id == last_cfg.extends),
            None,
        )

        if parent is None:
            print_wrn(
                f"{last_cfg.name} tried to extend {last_cfg.extends} but it doesn't exists",  # noqa: E501
            )
            return configs

        try:
            if parent in configs:
                raise RecursionError
        except RecursionError:
            print_err(
                f"{last_cfg.name} tried to extend {last_cfg.extends} but it was extended before",  # noqa: E501
                True,
            )

        configs.append(parent)
        return cls._get_parents(get_all_instances, configs)


class BasicData(AbstractData[DataFileModel, BaseModel]):
    """Abstract data class for subclasses that use :class:`dotmix.data.DataFileModel` as it
    file data model and :class:`pydantic.BaseModel` as its (custom) data type
    """

    def load_data_file(self):
        self.file_data = load_toml_cfg_model(self.data_file_path, DataFileModel)

    def compute_data(self):
        if not self.file_data.custom:
            self.data = BaseModel.construct(**{})
            return

        if not self.file_data.extends:
            self.data = BaseModel.construct(**self.file_data.custom)

        data_dict = {}
        for parent in reversed(self.parents):
            data_dict = deep_merge(data_dict, parent.file_data.custom)

        self.data = BaseModel.construct(**data_dict)

    def print_data(self):
        print_key_values(self.data.dict())


# Functions:


@cache
def get_data_files(dir: Path) -> DataFilesDict:
    """ "Generic" function to get all the data files in a directory.

    Every submodule that defines a data class should define a function that calls this
    function with a specific ``dir`` parameter.

    This function sets the ID for each instance using the filename minus the extension

    :param dir: Path to the directory with the data files
    """

    files_dict: DataFilesDict = {}

    files = [f for f in os.listdir(dir) if re.match(r".*\.toml", f)]

    for file in files:
        path = Path(dir / file)

        cfg = load_toml_cfg(Path(dir / file))
        name = cfg["name"]
        id = path.with_suffix("").name

        if cfg and name:
            files_dict[id] = {"id": id, "path": path, "name": name}

    return files_dict


def get_data_by_id(
    id: str, files: DataFilesDict, cls: Type[DataClassType]
) -> Optional[DataClassType]:
    """Generic function to get a specific data class instance by id (unique).

    Every submodule that defines a data class should define a function that calls this
    function with specific ``files`` and ``cls`` parameters.

    :param id: The id string that identifies the data class instance
    :param files: :data:`dotmix.data.DataFilesDict` returned by
        :func:`dotmix.data.get_data_files`
    :param cls: Concrete class to construct the data instance
    """
    try:
        file = files[id]
        id = file["id"]
        name = file["name"]
        path = file["path"]
        return cls(id, name, path)
    except KeyError:
        print_err(f'{cls.__name__} "{id}" not found')


def get_all_data_instances(
    files: DataFilesDict, getter: GenericDataGetter[DataClassType]
) -> Dict[str, DataClassType]:
    """Generic function that returns all instances of a data class.

    Every submodule that defines a data class should define a function that calls this
    function with specific ``files`` and ``getter`` parameters.

    :param files: :data:`dotmix.data.DataFilesDict` returned by
        :func:`dotmix.data.get_data_files`
    :param getter: Generic function that calls :func:`dotmix.data.get_data_by_id` to
        return a data class instance
    """

    cfgs = {}

    for name in files.keys():
        c = getter(name)
        if c:
            cfgs[name] = c

    return cfgs
