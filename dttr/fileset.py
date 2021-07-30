import os
from functools import cached_property
from pathlib import Path
from typing import Dict, List, Optional

import click
from pydantic import BaseModel

from dttr.utils.abstractcfg import AbstractConfig, BaseSchema

from .config import get_data_dir
from .utils import (
    SettingsDict,
    deep_merge,
    get_all_configs,
    get_config_by_id,
    load_toml_cfg,
    load_toml_cfg_model,
)


class FileModel(BaseModel):
    id: str
    path: Path
    fileset: "FileSet"

    class Config:
        arbitrary_types_allowed = True


FileModelDict = Dict[str, FileModel]


class FileSet(AbstractConfig[BaseSchema, FileModelDict]):
    def load_cfg(self):
        self._cfg = load_toml_cfg_model(self.cfg_file, BaseSchema)

    @cached_property
    def parents(self) -> List["FileSet"]:
        return self._get_parents(get_filesets, [self])

    def compute_data(self) -> None:
        if not self.cfg.extends:
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
    files_settings: SettingsDict = {}

    for dir in files_dir.iterdir():
        path = dir / "settings.toml"

        if path.exists():
            cfg = load_toml_cfg(path)
            name = cfg["name"]
            id = dir.name

            if cfg and name:
                files_settings[id] = {"id": id, "path": path, "name": name}

    return files_settings


def get_filesets() -> Dict[str, FileSet]:
    return get_all_configs(get_fileset_settings(), get_fileset_by_id)


def get_fileset_by_id(id: str) -> Optional[FileSet]:
    return get_config_by_id(id, get_fileset_settings(), FileSet)


def get_paths_from_fileset(f: FileSet) -> Dict[str, FileModel]:
    files: Dict[str, FileModel] = {}
    dir = f.cfg_file.parent
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
