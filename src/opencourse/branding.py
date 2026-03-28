from rich.panel import Panel
from rich.text import Text

BANNER = r"""
  ____                    _____
 / __ \____  ___  ____   / ___/___  __  _____________
/ / / / __ \/ _ \/ __ \  \__ \/ _ \/ / / / ___/ ___/
/ /_/ / /_/ /  __/ / / / ___/ /  __/ /_/ / /  (__  )
\____/ .___/\___/_/ /_/ /____/\___/\__,_/_/  /____/
    /_/
"""


def banner_panel() -> Panel:
    title = Text("OpenCourse", style="bold bright_cyan")
    subtitle = Text("Terminal-First University Learning", style="cyan")
    body = Text(BANNER, style="bright_green")
    body.append("\nBig Data Processing Module Loaded", style="bright_black")
    return Panel(body, title=title, subtitle=subtitle, border_style="cyan", padding=(1, 2))
