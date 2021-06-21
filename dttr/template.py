import os
from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import BaseModel

from .config import get_data_dir
from .utils import load_toml_cfg


class TemplateConfig(BaseModel):
    name: str
    extends: Optional[str]


class Template:
    name: str
    cfg: TemplateConfig
    dir: Path

    def __init__(self, cfg, dir):
        self.cfg = cfg
        self.dir = dir
        self.name = cfg.name

    def __str__(self):
        return self.cfg.name


TemplateFile = Tuple[str, Path]


def get_templates_dir() -> Path:
    return get_data_dir() / "templates"


def get_templates() -> List[Template]:
    templates_dir = get_templates_dir()

    templates: List[Template] = []

    for dir in os.listdir(templates_dir):
        path = templates_dir / dir
        if not path.is_dir():
            continue

        cfg = load_toml_cfg(templates_dir / dir, "template.toml", TemplateConfig)

        if cfg is None:
            continue

        if cfg.name:
            entry = Template(cfg, path)
            templates.append(entry)

    return templates


def get_template_files(t: Template) -> List[TemplateFile]:
    files: List[TemplateFile] = []
    for (dirpath, _, filenames) in os.walk(t.dir):
        if len(filenames) == 0:
            continue

        dir_path = Path(dirpath)

        absolute_paths: List[Path] = []
        absolute_paths.extend(
            map(lambda f: dir_path.joinpath(f), filenames),
        )

        for path in absolute_paths:
            files.append((str(path.relative_to(t.dir)), path))

    return files
