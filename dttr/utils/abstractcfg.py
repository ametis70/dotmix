from abc import ABCMeta, abstractmethod
from functools import cached_property
from pathlib import Path
from pydantic import BaseModel
from typing import Dict, List, Callable, Optional, Type, Union, TypeVar, Generic
import click

A = TypeVar("A", bound="AbstractConfig")
S = TypeVar("S", bound="BaseSchema")
D = TypeVar("D", bound=Union[BaseModel, List, Dict])


class BaseSchema(BaseModel):
    name: str
    extends: Optional[str]
    custom: Optional[Dict[str, Union[str, bool, int, List, Dict]]]


class AbstractConfig(Generic[S, D], metaclass=ABCMeta):
    id: str
    name: str
    cfg_file: Path
    _data: Optional[D]
    _cfg: Optional[S]
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
    def cfg(self) -> Optional[S]:
        if not self._cfg:
            self.load_cfg()

        return self._cfg

    @cfg.setter
    def cfg(self, value: S) -> None:
        self._cfg = value

    @property
    def data(self):
        if not self._data:
            self.compute_data()

        return self._data

    @data.setter
    def data(self, value: D) -> None:
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
    def parents(self) -> List[A]:
        """Get parents recursively"""
        pass

    @classmethod
    def _get_parents(
        cls: Type[A],
        get_all_configs: Callable[[], Dict[str, A]],
        configs: List[A],
    ) -> List[A]:
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
