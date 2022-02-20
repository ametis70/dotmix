<p align="center" width="100%">
    <img width="50%" src="https://github.com/ianmethyst/dotmix/blob/main/docs/logo.svg" alt="dotmix's logo" />
</p>

dotmix is a template based solution to managing your dotfiles

# How it works

dotmix uses several configuration files to specify keys and values that will replace placeholders in your dotfiles to
modify them all at once and with minimal effort. This enables changing colors, layout and typographic variables quickly
in multiple programs without digging in all the configuration files (more than once) and keeping different "themes" that
go beyond what a GTK theme or a terminal colorscheme alone can offer in terms of customizability.

It also supports hooks that run before and after the file processing to make other operations like making symlinks or
reloading your window manager to make the changes in the configuration effective.

## Formats

For the time being, dotmix supports [TOML](https://toml.io/en/) as its configuration file format and
[moustache](https://mustache.github.io/) as its templating system.

## Configuration

Configuration files are split into 3 categories to allow modifying different parts of the dotfiles independently:

| Category | Examples of what could change                                    |
|----------|------------------------------------------------------------------|
| Color    | Colors for terminals, colorscheme for text editors, etc.         |
| Font     | Fonts for terminal, fonts for GUI aplications, icons font, etc.  |
| Theme    | Layout variables (padding, margins), GTK theme, icon theme, etc. |

These categories are arbitrary, and you can put all the variables in your theme file for example, if you prefer that
approach.

## Presets

If you have a combination of colors, fonts or theme variables that are meant to go together, you can define a preset
that will enable to set apply them your template without having to specify all the config files independently.

## Composability

Any color, font or theme config file can extend other configs to make changing related configs (i.e configs that share
variables) a simple task.
