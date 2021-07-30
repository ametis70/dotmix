from colp import HEX, Color
from colp.conversion import RGB

# NOTE: Monkey patching colp's Color.MODE
Color.MODE = "css"  # type: ignore
HEX = HEX
RGB = RGB
