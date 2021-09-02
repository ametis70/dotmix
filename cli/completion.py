from click import ParamType
from click.shell_completion import CompletionItem

from dttr.appearance import get_appearances
from dttr.colorscheme import get_colorschemes
from dttr.fileset import get_filesets
from dttr.runner import get_hooks
from dttr.typography import get_typographies


class IdType(ParamType):
    name = "ID"


class AppearanceType(IdType):
    def shell_complete(self, ctx, param, incomplete):
        appearances = get_appearances()

        ids = [c.id for c in appearances.values()]

        return [CompletionItem(name) for name in ids if name.startswith(incomplete)]


class ColorschemeType(IdType):
    def shell_complete(self, ctx, param, incomplete):
        colorschemes = get_colorschemes()

        ids = [c.id for c in colorschemes.values()]

        return [CompletionItem(name) for name in ids if name.startswith(incomplete)]


class FilesetType(IdType):
    def shell_complete(self, ctx, param, incomplete):
        filesets = get_filesets()

        ids = [c.id for c in filesets.values()]

        return [CompletionItem(name) for name in ids if name.startswith(incomplete)]


class TypographyType(IdType):
    def shell_complete(self, ctx, param, incomplete):
        typographies = get_typographies()

        ids = [c.id for c in typographies.values()]

        return [CompletionItem(name) for name in ids if name.startswith(incomplete)]


class HookType(IdType):
    def shell_complete(self, ctx, param, incomplete):
        hooks = get_hooks()

        return [CompletionItem(name) for name in hooks if name.startswith(incomplete)]
