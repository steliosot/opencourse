from rich.panel import Panel
from rich.text import Text

LOGO = r"""
  ____                  ______
 / __ \____  ___  ____ / ____/___  __  ________________
/ / / / __ \/ _ \/ __ `/ /   / __ \/ / / / ___/ ___/ _ \
/ /_/ / /_/ /  __/ /_/ / /___/ /_/ / /_/ / /  (__  )  __/
\____/ .___/\___/\__,_/\____/\____/\__,_/_/  /____/\___/
    /_/
"""

ARISTOTLE_ICON = r'''
           .-""""-.
         .'  .--.  '.
        /   (o  o)   \
       |      /\      |
       |  .-.(  ).-.  |
        \  \  "--" / /
         '._'----'_.'
           /  ||  \
          /___||___\
'''


def banner_panel() -> Panel:
    title = Text("OpenCourse", style="bold bright_cyan")
    subtitle = Text("Terminal-First University Learning", style="cyan")
    body = Text(LOGO, style="bold bright_cyan")
    return Panel(body, title=title, subtitle=subtitle, border_style="cyan", padding=(1, 2))
