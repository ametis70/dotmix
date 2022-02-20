""" Module for running dotmix. This module contains functions to work with the template
    engine, computing checksums and running hooks"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, List, Optional, cast

import chevron
import click

from dotmix.appearance import Appearance, get_appearance_by_id
from dotmix.colorscheme import Colorscheme, get_colorscheme_by_id
from dotmix.config import DefaultSettingType, get_data_dir, get_default_setting
from dotmix.data import DataClassType, GenericDataGetter
from dotmix.fileset import FileModel, Fileset, get_fileset_by_id
from dotmix.typography import Typography, get_typography_by_id
from dotmix.utils import (
    get_verbose,
    print_err,
    print_key_values,
    print_pair,
    print_verbose,
    print_wrn,
)


def get_out_dir() -> Path:
    """Get the output files directory.

    :returns: Output directory
    """
    return get_data_dir() / "out"


def get_checksums_file() -> Path:
    """Get the checksums files.

    :returns: Checksums file
    """

    return get_data_dir() / ".checksums"


def get_out_backup_dir() -> Path:
    """Get the output backup directory.

    :returns: Output backup directory
    """

    return get_data_dir() / ".out.backup"


def get_hooks_dir() -> Path:
    """Get the hooks directory.

    :returns: Hook directory
    """

    return get_data_dir() / "hooks"


def get_hooks() -> List[str]:
    """Get hook filenames names (IDs).

    :returns: List of hooks IDs
    """
    func: Callable[[Path], str] = lambda p: p.name
    return list(map(func, get_hooks_dir().iterdir()))


def run_hook(hook: str) -> int:
    """Run a hook in a subprocess and return its return code

    The hook subprocess will be able to access the output directory through the
    ``$DOTMIX_OUT`` environment variable.

    :param hook: Filename of the hook

    :returns: Hook subprocess return code
    """

    return_code: int = 1
    hook_file = get_hooks_dir() / hook

    try:
        if not hook_file.exists:
            raise FileNotFoundError

        if not os.access(str(hook_file), os.X_OK):
            raise PermissionError

        os.environ["DOTMIX_OUT"] = str(get_out_dir())
        p = subprocess.run(hook_file)

        return_code = p.returncode

    except FileNotFoundError:
        print_err(f"Hook {hook_file} doesn't exist")
    except PermissionError:
        print_err(f"Wrong permissions on {hook_file}")
    finally:
        return return_code


def hash_file(file: Path) -> str:
    """Create a sha256 hash of a file

    :param file: File to hash

    :returns: Generated hash
    """
    with file.open("rb") as f:
        hash = hashlib.sha256(f.read()).hexdigest()
        return hash


def write_checksums() -> None:
    """Write hashes of output files to checksums file.

    .. warning::
        This function should be called only when running :func:`apply` because it is
        used to check for changes of the current output files. If called afterwards,
        there's risk of losing changes.
    """

    data_dir = get_data_dir()
    checksums = []
    for root, _, files in os.walk(get_out_dir()):
        for file in files:
            path = Path(root, file)
            checksums.append(f"{hash_file(path)} {path.relative_to(data_dir)}\n")

    with get_checksums_file().open("w") as f:
        f.writelines(checksums)


def verify_checksums() -> List[str]:
    """Verify checksums and return a list of modified files.

    :returns: List of modified files
    """
    data_dir = get_data_dir()
    modified_files = []

    file = get_checksums_file()
    if not file.exists():
        return []

    with get_checksums_file().open("r") as f:
        lines = f.readlines()
        for line in lines:
            digest, file = line.split()
            path = Path(data_dir, file)
            if path.exists():
                hash = hash_file(path)
                if hash != digest:
                    modified_files.append(file)

    return modified_files


def print_modified_files(modified_files: List[str]) -> None:
    """Pretty prints modified files.

    :param modified_files: This should be a list of files like the one returned by
    :func:`verify_checksums`
    """
    if modified_files:
        click.secho("The following files where modified:\n", fg="yellow")
        for file in modified_files:
            click.secho(file, fg="yellow")
        click.echo("")


def get_settings(
    field: DefaultSettingType,
    id: Optional[str],
    getter: GenericDataGetter[DataClassType],
    use_defaults: bool,
) -> Optional[DataClassType]:
    """Function to get a data instance from an ID (if specified) or its default value
        from the defaults configuration (if defined).

    The defaults configuration is defined in :mod:`dotmix.config`.

    :param field: Data file/class type
    :param id: ID of the data to get
    :param getter: Function to get the data class instance by ID
    :param use_defaults: Flag to determine if defaults should be used in case no ID is
        specified
    """
    if not id:
        if not use_defaults:
            print_wrn(f"Skipping {field} (No id provided and not using default)")
            return None

        default_id = get_default_setting(field)
        if not default_id:
            print_wrn(f"Skipping {field} (No id provided and default not set)")
            return None

        settings = getter(default_id)
        if not settings:
            return print_err(f"Invalid id for {field} from defaults", True)

        click.secho(f"Using default settings ({settings.id}) for {field} from defaults")
        return settings

    else:
        settings = getter(id)
        if not settings:
            return print_err(f"Settings {id} not found for {field}", True)

        return settings


def render_file(file: FileModel, relative_path: str, out_dir: str, vars: Dict) -> None:
    """Read template file and write output file.

    :param file: Template file from fileset
    :param relative_path: Relative path to root of fileset
    :param out_dir: Directory for output files
    :param vars: Input variables for the template engine
    """
    with open(file.path, "r") as f:
        out_file = Path(out_dir) / relative_path
        print_verbose(f"Rendering file: {str(out_file)}")
        rendered = cast(str, chevron.render(f, vars, warn=get_verbose()))
        os.makedirs(out_file.parent, exist_ok=True)
        with out_file.open("w", encoding="utf-8") as out:
            out.write(rendered)


def render_fileset(fileset: Fileset, out_dir: str, vars: Dict) -> None:
    """Render and write a complete fileset.

    :param fileset: Fileset to be rendered
    :param out_dir: Output files directory
    :param vars: Input variables for the tempalte engine
    """

    for relative_dir, file in fileset.data.items():
        render_file(file, relative_dir, out_dir, vars)


def merge_data(
    colorscheme: Optional[Colorscheme],
    typography: Optional[Typography],
    appearance: Optional[Appearance],
) -> Dict:
    """Merge variables from data instances and return a new dictionary

    :param colorscheme: Colorscheme model instance
    :param typography: Typography model instance
    :param appearance: Appearance model instance

    :returns: Dictionary with variables to be fed to the template engine
    """
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
) -> None:
    """Main function of dotmix.

    This will get the data instances , check for modified files, render files, write
    checksums and run hooks.


    :param colorscheme_id: ID for colorscheme
    :param fileset_id: ID for fileset
    :param appearance: ID for appearance
    :param typography: ID for typogrpahy
    :param pre_hook: Filename for pre_hook
    :param post_hook: Filename for post hook
    :param use_defaults: Flag to determine if defaults should be used
    :param force: Flag to force running even if files where modified
    :param interactive: If it's true, this function will ask for confirmation before
        running. This parameter is true when running from the CLI
    """

    fileset = get_settings("fileset", fileset_id, get_fileset_by_id, use_defaults)

    if not fileset:
        return print_err("No fileset specified", True)

    modified_files = verify_checksums()
    print_modified_files(modified_files)
    if modified_files and not force:
        return print_err(
            "Please discard the changes or run with -F/--force flag",
            True,
        )

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

    click.echo("Running dotmix with the following settings:\n")
    print_pair("Fileset", f"{fileset.name} ({fileset.id})")
    if colorscheme:
        print_pair("Colorscheme", f"{colorscheme.name} ({colorscheme.id})")
    if appearance:
        print_pair("Appearance", f"{appearance.name} ({appearance.id})")
    if typography:
        print_pair("Typography", f"{typography.name} ({typography.id})")
    if pre_hook:
        print_pair("Pre hook", pre_hook)
    if post_hook:
        print_pair("Post hook", post_hook)

    click.echo("")

    if get_verbose():
        fileset.print_data()
        for key, d in vars.items():
            click.secho(f"Variables from {key}:\n", bold=True, fg="blue")
            print_key_values(d)
            click.echo("")

    if interactive:
        overwrite_text = (
            "(Modified files will be overwritten)" if force and modified_files else ""
        )
        if click.confirm(f"Continue? {overwrite_text}", abort=True):
            pass
    elif not interactive and get_verbose():
        click.echo("Info: Running non-interactively")

    click.echo("")

    with tempfile.TemporaryDirectory(prefix="dotmix_out") as tmp_dir:
        if fileset:
            render_fileset(fileset, tmp_dir, vars)

        if pre_hook:
            click.echo(f"Running pre hook: {pre_hook}")
            code = run_hook(pre_hook)
            if code != 0:
                return print_err(f"Hook {pre_hook} finished with an error", True)

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
                print_err(f"Hook {post_hook} finished with an error")
                click.echo("Restoring backup of out files")
                shutil.move(backup_dir, out_dir)
                sys.exit(1)

        click.echo("Computing checksums\n")
        write_checksums()
        click.secho("Done!", fg="green", bold=True)
