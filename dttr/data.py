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
)

from pydantic import BaseModel

from dttr.utils import (
    deep_merge,
    load_toml_cfg,
    load_toml_cfg_model,
    print_err,
    print_key_values,
    print_wrn,
)

DataClassType = TypeVar("DataClassType", bound="AbstractData")
DataFileModelType = TypeVar("DataFileModelType", bound="DataFileModel")
DataType = TypeVar("DataType", bound=Union[TypedDict, BaseModel, Dict])
GenericDataGetter = Callable[[str], Optional[DataClassType]]
CustomDictTypes = Union[str, bool, int, List, Dict]


class DataFileModel(BaseModel):
    name: str
    extends: Optional[str]
    custom: Optional[Dict[str, CustomDictTypes]]


class AbstractData(Generic[DataFileModelType, DataType], metaclass=ABCMeta):
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
        pass

    @property
    def file_data(self) -> Optional[DataFileModelType]:
        if not self._file_data:
            self.load_data_file()

        return self._file_data

    @file_data.setter
    def file_data(self, value: DataFileModelType) -> None:
        self._file_data = value

    @property
    def data(self):
        if not self._computed_data:
            self.compute_data()

        return self._computed_data

    @data.setter
    def data(self, value: DataType) -> None:
        self._computed_data = value

    @abstractmethod
    def compute_data(self):
        """Populate `data` property with the values this class expects"""
        pass

    @abstractmethod
    def print_data():
        """Pretty prints the data from this instance"""
        pass

    @cached_property
    @abstractmethod
    def parents(self) -> List[DataClassType]:
        """Get parents recursively"""
        pass

    @classmethod
    def _get_parents(
        cls: Type[DataClassType],
        get_all_instances: Callable[[], Dict[str, DataClassType]],
        configs: List[DataClassType],
    ) -> List[DataClassType]:
        """Filters list returned by `get_all_configs()` that are parents.

        This is meant to be called in `parents` property getter with a
        `get_all_configs` function that returns the config files that can be
        used with this particular class
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


class DataFileMetadata(TypedDict):
    id: str
    name: str
    path: Path


DataFilesDict = Dict[str, DataFileMetadata]


@cache
def get_data_files(dir: Path) -> DataFilesDict:

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
    cfgs = {}

    for name in files.keys():
        c = getter(name)
        if c:
            cfgs[name] = c

    return cfgs
