from abc import ABCMeta, abstractmethod
from functools import cached_property
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

import click
from pydantic import BaseModel

AbstractConfigType = TypeVar("AbstractConfigType", bound="AbstractConfig")
BaseSchemaType = TypeVar("BaseSchemaType", bound="BaseSchema")
DataType = TypeVar("DataType", bound=Union[TypedDict, BaseModel, List, Dict])

CustomDictTypes = Union[str, bool, int, List, Dict]


class BaseSchema(BaseModel):
    name: str
    extends: Optional[str]
    custom: Optional[Dict[str, CustomDictTypes]]


class AbstractConfig(Generic[BaseSchemaType, DataType], metaclass=ABCMeta):
    id: str
    name: str
    cfg_file: Path
    _data: Optional[DataType]
    _cfg: Optional[BaseSchemaType]
    _parents: Optional[List[BaseModel]]

    def __init__(self, id: str, name: str, cfg_file: Path):
        self.id = id
        self.name = name
        self.cfg_file = cfg_file

        self._cfg = None
        self._data = None
        self._parents = None

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}>"

    @abstractmethod
    def load_cfg() -> None:
        pass

    @property
    def cfg(self) -> Optional[BaseSchemaType]:
        if not self._cfg:
            self.load_cfg()

        return self._cfg

    @cfg.setter
    def cfg(self, value: BaseSchemaType) -> None:
        self._cfg = value

    @property
    def data(self):
        if not self._data:
            self.compute_data()

        return self._data

    @data.setter
    def data(self, value: DataType) -> None:
        self._data = value

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
    def parents(self) -> List[AbstractConfigType]:
        """Get parents recursively"""
        pass

    @classmethod
    def _get_parents(
        cls: Type[AbstractConfigType],
        get_all_configs: Callable[[], Dict[str, AbstractConfigType]],
        configs: List[AbstractConfigType],
    ) -> List[AbstractConfigType]:
        """Filters list returned by `get_all_configs()` that are parents.

        This is meant to be called in `parents` property getter with a
        `get_all_configs` function that returns the config files that can be
        used with this particular class
        """
        last_cfg = configs[-1].cfg

        if not last_cfg.extends:
            return configs

        parent = next(
            (c for c in get_all_configs().values() if c.id == last_cfg.extends),
            None,
        )

        if parent is None:
            click.secho(
                f"Warning: {last_cfg.name} tried to extend {last_cfg.extends} but it doesn't exists",  # noqa: E501
                err=True,
                fg="yellow",
            )
            return configs

        try:
            if parent in configs:
                raise RecursionError
        except RecursionError:
            click.secho(
                f"Error: {last_cfg.name} tried to extend {last_cfg.extends} but it was extended before",  # noqa: E501
                err=True,
                fg="red",
            )

        configs.append(parent)
        return cls._get_parents(get_all_configs, configs)
