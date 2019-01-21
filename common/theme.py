
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPalette


def get_light_bg(widget: QtWidgets.QWidget) -> str:
    """
    returns the color name for the widgets `QPalette.Light` palette
    """
    return widget.palette().color(QPalette.Light).name()

def get_dark_bg(widget: QtWidgets.QWidget) -> str:
    """
    returns the color name for the widgets `QPalette.Dark` palette
    """
    return widget.palette().color(QPalette.Dark).name()

def set_dark_rounded_css(widget: QtWidgets.QWidget) -> str:
    """
    set a widget stylesheet string which sets a rounded border and background color
    """
    bg = get_dark_bg(widget)
    widget.setStyleSheet( UI_DARK_ROUND_CSS % ( bg, bg ) )

BG_COLOR_MANUAL = "#ff5d00"
BG_COLOR_AUTO = "#0000ff"

UI_QLABEL_BG_CSS = "QLabel { \
    color: white; \
    background-color: %s \
}"

UI_DARK_ROUND_CSS = "QWidget { \
    background-color: %s; \
    border-style: solid; \
    border-color: %s; \
    border-width: 2px; \
    border-radius: 3px; \
}"