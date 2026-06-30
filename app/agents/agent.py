"""
Base Agent class for the Price Is Right multi-agent framework.
Provides shared logging infrastructure with ANSI color support.
"""
import logging


class Agent:
    """
    Abstract superclass for all Agents in the Price Is Right framework.
    Provides colored logging so each agent's output is visually distinct
    in the terminal and the Gradio log panel.
    """

    # Foreground colors
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Background color
    BG_BLACK = '\033[40m'

    # Reset code to return to default color
    RESET = '\033[0m'

    name: str = ""
    color: str = '\033[37m'

    def log(self, message: str) -> None:
        """
        Log this as an info message, identifying the agent by name and color.
        :param message: the message to log
        """
        color_code = self.BG_BLACK + self.color
        formatted = f"[{self.name}] {message}"
        logging.info(color_code + formatted + self.RESET)
