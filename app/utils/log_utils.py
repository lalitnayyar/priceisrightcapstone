"""
Log formatting utilities for the Price Is Right dashboard.

Converts ANSI terminal color escape codes to HTML <span> tags so that
agent log messages display with color in the Gradio HTML panel.
"""
from typing import List

# ANSI escape code constants (must match those in agent.py)
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'
BG_BLACK = '\033[40m'
BG_BLUE = '\033[44m'
RESET = '\033[0m'

# Mapping from ANSI code combinations to HTML hex colors
COLOR_MAP = {
    BG_BLACK + RED:     "#dd0000",
    BG_BLACK + GREEN:   "#00dd00",
    BG_BLACK + YELLOW:  "#dddd00",
    BG_BLACK + BLUE:    "#0000ee",
    BG_BLACK + MAGENTA: "#aa00dd",
    BG_BLACK + CYAN:    "#00dddd",
    BG_BLACK + WHITE:   "#87CEEB",
    BG_BLUE + WHITE:    "#ff7800",
}


def reformat(message: str) -> str:
    """
    Replace ANSI escape codes in a log message with HTML color spans.
    :param message: raw log message with ANSI codes
    :return: HTML-formatted message string
    """
    for ansi_code, hex_color in COLOR_MAP.items():
        message = message.replace(ansi_code, f'<span style="color: {hex_color}">')
    message = message.replace(RESET, '</span>')
    return message


def html_for(log_data: List[str], max_lines: int = 18) -> str:
    """
    Render the last N log lines as a scrollable HTML div.
    :param log_data: list of formatted HTML log lines
    :param max_lines: number of recent lines to display
    :return: HTML string for the Gradio HTML component
    """
    output = "<br>".join(log_data[-max_lines:])
    return (
        '<div id="scrollContent" style="'
        'height: 400px; overflow-y: auto; border: 1px solid #ccc; '
        'background-color: #222229; padding: 10px; font-family: monospace; font-size: 12px;">'
        f'{output}'
        '</div>'
    )
