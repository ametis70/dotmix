import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple
import click

from pydantic import BaseModel

from .config import get_data_dir
from .utils import load_toml_cfg


class TemplateConfig(BaseModel):
    name: str
    extends: Optional[str]


class Template:
    def __init__(self, cfg, dir):
        self.cfg: TemplateConfig = cfg
        self.dir: Path = dir
        self.name: str = cfg.name

    def __str__(self):
        return self.name


TemplateFile = Tuple[str, Path, Template]


def get_templates_dir() -> Path:
    return get_data_dir() / "templates"


@lru_cache
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


def get_template_by_name(name: str) -> Optional[Template]:
    templates = get_templates()

    t = next(filter(lambda t: t.name == name, templates), None)

    if t is not None:
        return t

    print(f'Template with name "{name}" not found')


def get_template_files(t: Template) -> List[TemplateFile]:
    files: List[TemplateFile] = []
    for (dirpath, _, filenames) in os.walk(t.dir):
        if not filenames or any(map(lambda f: f == "template.toml", filenames)):
            # Skip any files in root directory (i.e. files alongside template.toml)
            continue

        dir_path = Path(dirpath)

        absolute_paths: List[Path] = []
        absolute_paths.extend(
            map(lambda f: dir_path.joinpath(f), filenames),
        )

        for path in absolute_paths:
            files.append((str(path.relative_to(t.dir)), path, t))

    return files


def get_extended_templates(templates: List[Template]) -> List[Template]:
    """Get extended templates recursively"""
    template = templates[-1].cfg

    if template.extends:
        all_templates = get_templates()
        extended = next(
            filter(lambda t: t.name == template.extends, all_templates), None
        )

        if extended is not None:
            if extended in templates:
                raise RecursionError(
                    f"{template.name} tried to extend \
{template.extends} but it was extended before"
                )

            templates.append(extended)
            return get_extended_templates(templates)
        else:
            print(
                f"Warning: {template.name} tried to extend \
{template.extends} but it doesn't exists"
            )

    return templates


def add_or_replace_files(original: List[TemplateFile], new: List[TemplateFile]):
    original_dict = dict({f[0]: f for f in original})
    new_dict = dict({f[0]: f for f in new})

    original_dict.update(new_dict)

    return list(original_dict.values())


def get_merged_template_from_extends(
    t: Template,
) -> Tuple[List[TemplateFile], List[Template]]:
    """Merge templates files and return them with the list of templates merged"""
    templates = get_extended_templates([t])

    files: List[TemplateFile] = []

    for template in reversed(templates):
        files = add_or_replace_files(files, get_template_files(template))

    return (files, templates)


def print_merged_template_files(merged: Tuple[List[TemplateFile], List[Template]]):
    """Pretty prints the result from get_merged_template_from_extends"""

    files = merged[0].copy()
    templates = merged[1]

    for i, template in enumerate(templates):
        click.secho(
            f"Files {'' if i == 0 else 'inherited '}from template {template}\n",
            fg="blue",
            bold=True,
        )

        for index, file in enumerate(files):
            newline = index == len(files) - 1
            if file[2].name == template.name:
                click.secho(f"  {file[0]}")
                del files[index]

            if newline:
                click.echo("")
