from typing import Optional

from pydantic import BaseModel


class Base16Colorscheme(BaseModel):
    base00: Optional[str]
    base01: Optional[str]
    base02: Optional[str]
    base03: Optional[str]
    base04: Optional[str]
    base05: Optional[str]
    base06: Optional[str]
    base07: Optional[str]
    base08: Optional[str]
    base09: Optional[str]
    base0A: Optional[str]
    base0B: Optional[str]
    base0C: Optional[str]
    base0D: Optional[str]
    base0E: Optional[str]
    base0F: Optional[str]


class TerminalColorscheme(BaseModel):
    bg: Optional[str]
    fg: Optional[str]
    color0: Optional[str]
    color1: Optional[str]
    color2: Optional[str]
    color3: Optional[str]
    color4: Optional[str]
    color5: Optional[str]
    color6: Optional[str]
    color7: Optional[str]
    color8: Optional[str]
    color9: Optional[str]
    color10: Optional[str]
    color11: Optional[str]
    color12: Optional[str]
    color13: Optional[str]
    color14: Optional[str]
    color15: Optional[str]


class ParsedColorschemes(BaseModel):
    terminal: TerminalColorscheme
    base16: Base16Colorscheme


class DttrColorscheme(BaseModel):
    bg: str
    light_bg: str
    selection: str
    comment: str
    dark_fg: str
    fg: str
    light_fg: str
    lighter_bg: str

    red: str
    orange: str
    yellow: str
    green: str
    blue: str
    cyan: str
    magenta: str
    brown: str

    alt_red: str
    alt_orange: str
    alt_yellow: str
    alt_green: str
    alt_blue: str
    alt_cyan: str
    alt_magenta: str
    alt_brown: str
