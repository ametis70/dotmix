import os
from functools import cached_property
from pathlib import Path
from typing import Dict, List, Optional

import click
from pydantic import BaseModel

from dttr.data import (
    AbstractData,
    DataFileModel,
    DataFilesDict,
    get_all_data_instances,
    get_data_by_id,
)

from .config import get_data_dir
from .utils import deep_merge, load_toml_cfg, load_toml_cfg_model


class FileModel(BaseModel):
    id: str
    path: Path
    fileset: "Fileset"

    class Config:
        arbitrary_types_allowed = True


FileModelDict = Dict[str, FileModel]


class Fileset(AbstractData[DataFileModel, FileModelDict]):
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
    return get_data_dir() / "templates"


def get_fileset_settings():
    files_dir = get_filesets_dir()
    files_settings: DataFilesDict = {}

    for dir in files_dir.iterdir():
        path = dir / "settings.toml"

        if path.exists():
            cfg = load_toml_cfg(path)
            name = cfg["name"]
            id = dir.name

            if cfg and name:
                files_settings[id] = {"id": id, "path": path, "name": name}

    return files_settings


def get_filesets() -> Dict[str, Fileset]:
    return get_all_data_instances(get_fileset_settings(), get_fileset_by_id)


def get_fileset_by_id(id: str) -> Optional[Fileset]:
    return get_data_by_id(id, get_fileset_settings(), Fileset)


def get_paths_from_fileset(f: Fileset) -> Dict[str, FileModel]:
    files: Dict[str, FileModel] = {}
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
