import click

from dotmix.appearance import get_appearance_by_id, get_appearances
from dotmix.colorscheme import get_colorscheme_by_id, get_colorschemes
from dotmix.config import create_config, get_current_theme, scaffold_data_path
from dotmix.fileset import get_fileset_by_id, get_filesets
from dotmix.runner import apply
from dotmix.typography import get_typographies, get_typography_by_id
from dotmix.utils import print_err, set_verbose

from .completion import (
    AppearanceType,
    ColorschemeType,
    FilesetType,
    HookType,
    TypographyType,
)
from .utils import print_setting_names


@click.group()
def cli():
    pass


# Config


@cli.group()
def config():
    """Configure dotmix"""


@config.command("init")
@click.option(
    "--force",
    "-f",
    is_flag=True,
)
def init(force):
    """Initialize dotmix config and data directory"""
    if force and click.confirm(
        "Are you sure you want to recreate the default config?", abort=True
    ):
        pass

    click.echo(f"{'Rei' if force else 'I'}ntializing config")
    create_config(force=force)
    click.echo("Creating data directories")
    scaffold_data_path()


# Fileset


@cli.group()
def fileset():
    """Manage filesets"""


@fileset.command("list")
def fileset_list():
    """Show fileset names and IDs"""
    print_setting_names(get_filesets)


@fileset.command("show")
@click.argument("fileset", type=FilesetType())
def fileset_show(fileset):
    """List files from fileset"""
    get_fileset_by_id(fileset).print_data()


# Colorscheme


@cli.group()
def colorscheme():
    """Manage colorschemes"""


@colorscheme.command("list")
def colorscheme_list():
    """Show colorscheme names and IDs"""
    print_setting_names(get_colorschemes)


@colorscheme.command("show")
@click.argument("id", type=ColorschemeType())
def colorscheme_show(id):
    """Display colors from colorscheme"""
    get_colorscheme_by_id(id).print_data()


# Typography


@cli.group()
def typography():
    """Manage typographies"""


@typography.command("list")
def typography_list():
    """Show typography names and IDs"""
    print_setting_names(get_typographies)


@typography.command("show")
@click.argument("id", type=TypographyType())
def typography_show(id):
    """Display variables from typography"""
    get_typography_by_id(id).print_data()


# Appearance


@cli.group()
def appearance():
    """Manage appearances"""


@appearance.command("list")
def appearance_list():
    """Show appearances names and IDs"""
    print_setting_names(get_appearances)


@appearance.command("show")
@click.argument("id", type=AppearanceType())
def appearance_show(id):
    """Display variables from appearance"""
    get_appearance_by_id(id).print_data()


# Apply


@cli.command("apply")
@click.option("--fileset", "-f", type=FilesetType())
@click.option("--typography", "-t", type=TypographyType())
@click.option("--appearance", "-a", type=AppearanceType())
@click.option("--colorscheme", "-c", type=ColorschemeType())
@click.option("--pre", type=HookType(), help="Pre hook ID")
@click.option("--post", type=HookType(), help="Post hook ID")
@click.option(
    "--no-defaults",
    "-N",
    is_flag=True,
    help="Disable default data from configuration",
    default=False,
)
@click.option("--force", "-F", is_flag=True, help="Run even if files changed")
@click.option("--verbose", "-v", is_flag=True, help="Print additional information")
@click.option(
    "--reapply", "-r", is_flag=True, help="Run with last applied theme/settings"
)
def cli_apply(
    fileset,
    typography,
    appearance,
    colorscheme,
    pre,
    post,
    no_defaults,
    force,
    verbose,
    reapply,
):
    """Generate output files from fileset and data"""

    if verbose:
        set_verbose(True)

    if reapply:
        current = get_current_theme()
        if not current:
            return print_err(
                "There are no theme or settings stored. Run without -r/--reapply", True
            )

        current_dict = current.dict()

        fileset = current_dict.get("fileset") or fileset
        typography = current_dict.get("typography") or typography
        appearance = current_dict.get("appearance") or appearance
        colorscheme = current_dict.get("colorscheme") or colorscheme
        pre = current_dict.get("pre_hook") or pre
        post = current_dict.get("post_hook") or post

    apply(
        fileset_id=fileset,
        typography_id=typography,
        appearance_id=appearance,
        colorscheme_id=colorscheme,
        pre_hook=pre,
        post_hook=post,
        use_defaults=not no_defaults,
        force=force,
        interactive=True,
    )
