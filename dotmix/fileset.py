"""Data module for filesets"""

import os
from functools import cached_property
from pathlib import Path
from typing import Dict, List, Optional

import click
from pydantic import BaseModel

from dotmix.data import (
    AbstractData,
    DataFileModel,
    DataFilesDict,
    get_all_data_instances,
    get_data_by_id,
)

from .config import get_data_dir
from .utils import deep_merge, load_toml_cfg, load_toml_cfg_model


class FileModel(BaseModel):
    """Model for individual files

    :param id: Unique id that identifies the file. Can be used to detect collisions
        between a fileset instance and its parents
    :param path: Absolute file path
    :param fileset: Fileset instance associated with this file
    """

    id: str
    path: Path
    fileset: "Fileset"

    class Config:
        arbitrary_types_allowed = True


FileModelDict = Dict[str, FileModel]
"""Dictionary of fileset files"""


class Fileset(AbstractData[DataFileModel, FileModelDict]):
    """Data class for filesets"""

    def load_data_file(self):
        self.file_data = load_toml_cfg_model(self.data_file_path, DataFileModel)

    @cached_property
    def parents(self) -> List["Fileset"]:
        return self._get_parents(get_filesets, [self])

    def compute_data(self) -> None:
        if not self.file_data.extends:
            self.data = get_paths_from_fileset(self)

        file_paths: FileModelDict = {}
        for p in reversed(self.parents):
            file_paths = deep_merge(file_paths, get_paths_from_fileset(p))

        self.data = file_paths

    def print_data(self):
        for p in reversed(self.parents):
            click.secho(
                f"Files {'' if p is self else 'inherited '}from {p.name}\n",
                fg="blue",
                bold=True,
            )

            for file in self.data.values():
                if file.fileset == p:
                    click.secho(f"  {file.id}")

            click.echo("")


FileModel.update_forward_refs()


def get_filesets_dir() -> Path:
    """Get filesets directory.

    :returns: Filesets directory
    """

    return get_data_dir() / "filesets"


def get_fileset_files():
    """Get filesets data files.

    :returns: Fileset data files dictionary
    """

    files_dir = get_filesets_dir()
    fileset_data_files: DataFilesDict = {}

    for dir in files_dir.iterdir():
        path = dir / "settings.toml"

        if path.exists():
            cfg = load_toml_cfg(path)
            name = cfg["name"]
            id = dir.name

            if cfg and name:
                fileset_data_files[id] = {"id": id, "path": path, "name": name}

    return fileset_data_files


def get_filesets() -> Dict[str, Fileset]:
    """Get all fileset instances.

    :returns: Dict of fileset instances
    """

    return get_all_data_instances(get_fileset_files(), get_fileset_by_id)


def get_fileset_by_id(id: str) -> Optional[Fileset]:
    """Get a specific fileset instance by id.

    :param id: Id of the fileset to get
    :returns: Fileset instance
    """

    return get_data_by_id(id, get_fileset_files(), Fileset)


def get_paths_from_fileset(f: Fileset) -> FileModelDict:
    """Recusrively get all template files from fileset

    :param f: Fileset instance
    :returns: Dictionary of file models
    """
    files: FileModelDict = {}
    dir = f.data_file_path.parent
    for (dirpath, _, filenames) in os.walk(dir):
        if not filenames or any(map(lambda f: f == "settings.toml", filenames)):
            # Skip any files in root directory (i.e. files alongside template.toml)
            continue

        dir_path = Path(dirpath)

        absolute_paths: List[Path] = []
        absolute_paths.extend(
            map(lambda f: dir_path.joinpath(f), filenames),
        )

        for path in absolute_paths:
            id = str(path.relative_to(dir))
            files[id] = FileModel(id=id, path=path, fileset=f)

    return files
