import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, cast

import chevron
import click

from dttr.appearance import Appearance, get_appearance_by_id
from dttr.colorscheme.colorscheme import Colorscheme, get_colorscheme_by_id
from dttr.config import (
    DefaultSettingType,
    get_data_dir,
    get_default_setting,
    get_verbose,
)
from dttr.fileset import FileModel, FileSet, get_fileset_by_id
from dttr.typography import Typography, get_typography_by_id
from dttr.utils import A, GenericsSettingGetter, print_key_values, print_pair


def get_out_dir():
    return get_data_dir() / "out"


def get_checksums_file():
    return get_data_dir() / ".checksums"


def get_out_backup_dir():
    return get_data_dir() / ".out.backup"


def get_hooks_dir():
    return get_data_dir() / "hooks"


def run_hook(hook: str) -> int:
    return_code: int = 1
    hook_file = get_hooks_dir() / hook
    try:
        if not hook_file.exists:
            raise FileNotFoundError

        if not os.access(str(hook_file), os.X_OK):
            raise PermissionError

        p = subprocess.run(hook_file)

        return_code = p.returncode

    except FileNotFoundError:
        click.secho(f"Error: Hook {hook_file} doesn't exist", fg="red", err=True)
    except PermissionError:
        click.secho(f"Error: Wrong permissions on {hook_file}", fg="red", err=True)
    finally:
        return return_code


def hash_file(file: Path) -> str:
    with file.open("rb") as f:
        hash = hashlib.sha256(f.read()).hexdigest()
        return hash


def write_checksums() -> None:
    data_dir = get_data_dir()
    checksums = []
    for root, _, files in os.walk(get_out_dir()):
        for file in files:
            path = Path(root, file)
            checksums.append(f"{hash_file(path)} {path.relative_to(data_dir)}\n")

    with get_checksums_file().open("w") as f:
        f.writelines(checksums)


def verify_checksums() -> List[str]:
    data_dir = get_data_dir()
    modified_files = []

    with get_checksums_file().open("r") as f:
        lines = f.readlines()
        for line in lines:
            digest, file = line.split()
            path = Path(data_dir, file)
            hash = hash_file(path)
            if hash != digest:
                modified_files.append(file)

    return modified_files


def print_modified_files(modified_files: List[str]):
    if modified_files:
        click.secho("The following files where modified:\n", fg="yellow")
        for file in modified_files:
            click.secho(file, fg="yellow", err=True)


def get_settings(
    field: DefaultSettingType,
    id: Optional[str],
    getter: GenericsSettingGetter[A],
    use_defaults: bool,
) -> Optional[A]:
    if not id:
        if not use_defaults:
            click.secho(
                f"Warning: Skipping {field} (No id provided and not using default)"
            )
            return None

        default_id = get_default_setting(field)
        if not default_id:
            click.secho(
                f"Warning: Skipping {field} (No id provided and default not set)"
            )
            return None

        settings = getter(default_id)
        if not settings:
            click.secho(f"Error: Invalid id for {field} from defaults")
            sys.exit(1)

        click.secho(f"Using default settings ({settings.id}) for {field} from defaults")
        return settings

    else:
        settings = getter(id)
        if not settings:
            click.secho(f"Error: Settings {id} not found for {field}")
            sys.exit(1)

        return settings


def render_file(file: FileModel, reltaive_path: str, out_dir: str, vars: Dict):
    with open(file.path, "r") as f:
        rendered = cast(str, chevron.render(f, vars))
        out_file = Path(out_dir) / reltaive_path
        os.makedirs(out_file.parent, exist_ok=True)
        if get_verbose():
            click.echo(f"Rendering file: {str(out_file)}")
        with out_file.open("w", encoding="utf-8") as out:
            out.write(rendered)


def render_fileset(fileset: FileSet, out_dir: str, vars: Dict):
    for relative_dir, file in fileset.data.items():
        render_file(file, relative_dir, out_dir, vars)


def merge_data(
    colorscheme: Optional[Colorscheme],
    typography: Optional[Typography],
    appearance: Optional[Appearance],
):
    colorscheme_values = (
        {**colorscheme.data["colors"].dict(), **colorscheme.data["custom"]}
        if colorscheme
        else {}
    )

    appearance_values = {**appearance.data.dict()} if appearance else {}
    typography_values = {**typography.data.dict()} if typography else {}

    vars = {
        "colors": colorscheme_values,
        "appearance": appearance_values,
        "typography": typography_values,
    }

    return vars


def apply(
    *,
    colorscheme_id: Optional[str] = None,
    fileset_id: Optional[str] = None,
    appearance_id: Optional[str] = None,
    typography_id: Optional[str] = None,
    pre_hook: Optional[str] = None,
    post_hook: Optional[str] = None,
    use_defaults: bool = True,
    force: bool = False,
    interactive: bool = False,
):

    fileset = get_settings("fileset", fileset_id, get_fileset_by_id, use_defaults)

    if not fileset:
        click.secho("Error: No fileset specified")
        sys.exit(1)

    modified_files = verify_checksums()
    print_modified_files(modified_files)
    if not force:
        click.secho(
            "\nError: Please discard the changes or run with -f/--force flag",
            fg="red",
            err=True,
        )
        sys.exit(1)

    colorscheme = get_settings(
        "colorscheme", colorscheme_id, get_colorscheme_by_id, use_defaults
    )
    appearance = get_settings(
        "appearance", appearance_id, get_appearance_by_id, use_defaults
    )
    typography = get_settings(
        "typography", typography_id, get_typography_by_id, use_defaults
    )

    vars = merge_data(colorscheme, typography, appearance)

    click.echo("Running dttr with the following settings:\n")
    print_pair("Fileset", f"{fileset.name} ({fileset.id})")
    if colorscheme:
        print_pair("Colorscheme", f"{colorscheme.name} ({colorscheme.id})")
    if appearance:
        print_pair("Appearance", f"{appearance.name} ({appearance.id})")
    if typography:
        print_pair("Typography", f"{typography.name} ({typography.id})")
    click.echo("")

    if get_verbose():
        fileset.print_data()
        for key, d in vars.items():
            click.secho(f"Variables from {key}:\n", bold=True, fg="blue")
            print_key_values(d)
            click.echo("")

    if interactive:
        overwrite_text = (
            ""
            if not force and not modified_files
            else "(Previous files will be overwritten)"
        )
        if click.confirm(f"Continue? {overwrite_text}", abort=True):
            pass
    elif not interactive and get_verbose():
        click.echo("Info: Running non interactively")

    click.echo("")

    with tempfile.TemporaryDirectory(prefix="dttr_out") as tmp_dir:
        render_fileset(fileset, tmp_dir, vars)

        if pre_hook:
            click.echo(f"Running pre hook: {pre_hook}")
            code = run_hook(pre_hook)
            if code != 0:
                click.secho(
                    f"Error: Hook {pre_hook} finished with an error", fg="red", err=True
                )
                sys.exit(1)

        out_dir = get_out_dir()
        backup_dir = get_out_backup_dir()

        if backup_dir.exists():
            click.echo("Removing previous backup")
            shutil.rmtree(backup_dir)

        if out_dir.exists():
            click.echo("Making backup of output files")
            shutil.move(out_dir, backup_dir)

        click.echo("Copying new output files from temporary directory")
        shutil.copytree(tmp_dir, out_dir)

        if post_hook:
            click.echo(f"Running post hook: {post_hook}")
            code = run_hook(post_hook)
            if code != 0:
                click.secho(
                    f"Error: Hook {post_hook} finished with an error",
                    fg="red",
                    err=True,
                )
                click.echo("Restoring backup of out files")
                shutil.move(backup_dir, out_dir)
                sys.exit(1)

        click.echo("Computing checksums\n")
        write_checksums()
        click.secho("Done!", fg="green", bold=True)
