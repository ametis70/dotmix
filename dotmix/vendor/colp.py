"""This module is for monkey patching colp's ``Color.Mode``"""


from colp import HEX, Color
from colp.conversion import RGB

Color.MODE = "css"  # type: ignore
HEX = HEX
RGB = RGB
