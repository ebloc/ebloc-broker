#!/usr/bin/env python3

import pathlib
import textwrap
import threading
from rich import pretty, print_json  # noqa # print
from rich.console import Console
from rich.pretty import pprint
from rich.theme import Theme
from typing import Dict, Union

from rich.traceback import install

install()  # for rich, show_locals=True
# pretty.install()

# if False disable write into file for the process
# heads up applies this all libs imported this
IS_WRITE = True
DRIVER_LOG = None
IS_THREADING_MODE_PRINT = False
thread_log_files: Dict[str, str] = {}
custom_theme = Theme(
    {
        "b": "bold",
        "info": "bold magenta",  # "bold dim magenta"
        "alert": "bold red",
        "green": "#50fa7b",
        "yellow": "#f1fa8c",
        "red": "#ff5555",
        "purple": "#bd93f9",
        "orange": "#ffb86c",
        "cyan": "#8be9fd",
        "bg": "bold green",
        "bb": "bold blue",
        "m": "magenta",
        "w": "white",
        "cy": "cyan",
        "y": "yellow",
        "g": "green",
        "r": "red",
        "yob": "yellow on black blink",
        "ib": "italic #6272a4",
        "ic": "italic cyan",
        "or": "orange1",  # o does not work
        "pink": "#ff79c6",
    }
)
console = Console(
    theme=custom_theme,
    force_terminal=True,  # https://rich.readthedocs.io/en/latest/console.html#terminal-detection
    # force_interactive=False,
)


class QuietExit(Exception):
    """Exit quietly without printing the trace."""


class Chars:
    b_open = "[bold]{[/bold]"  # {
    b_close = "[bold]}[/bold]"  # }
    straight_line = "[green]│[/green]"  # │


class Style:
    B = BOLD = "\033[1m"
    E = END = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    GREENB = f"\033[32m{BOLD}"
    YELLOW = "\033[33m"
    YELLOWB = f"\033[33m{BOLD}"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    CYANB = f"\033[36m{BOLD}"
    WHITE = "\033[37m"
    UNDERLINE = "\033[4m"


class Log:
    """Color class.

    Find colors from: python -m rich
    """

    def __init__(self):
        super().__init__()
        self.IS_PRINT = True
        self.LOG_FILENAME: Union[str, pathlib.Path] = ""
        self.console: Dict[str, Console] = {}
        self.inner_bullets = ["==>", "#> ", "## ", " * ", "###", "** ", "***", " **"]

    # def halo_decorator(self):
    #     with Halo(text="Loading", spinner="line", placement="right"):
    #         time.sleep(6)
    def print_color(self, text: str, color=None, is_bold=True, end="\n", highlight=True) -> None:
        """Print string in color format."""
        if text[0:3] in self.inner_bullets:
            if color and text == "==> ":
                console.print(f"[bold][{color}]{text[0:3]}[{color}][/bold]", end="")
            else:
                console.print(f"[bb]{text[0:3]}[/bb]", end="")

            text = text[3:]
        elif text[0:2] == "E:":
            console.print("[bold red]E:[/bold red]", end="", highlight=highlight)
            text = text[2:]

        if is_bold:
            console.print(f"[bold][{color}]{text}[{color}][/bold]", end=end, highlight=highlight)
        else:
            if color in ("white", "", None) and "[" not in text:
                print(text, end=end)
            else:
                console.print(f"[{color}]{text}[/{color}]", end=end, highlight=highlight)

    def pre_color_check(self, text, color, is_bold):
        """Check color for substring."""
        text = str(text)
        _len = None
        is_bullet = False
        is_r = ""
        if text and text[0] == "\r":
            is_r = "\r"
            text = text[1:]

        if text.lower() in ["[ ok ]", "[  ok  ]"]:
            text = "[  [bold green]OK[/bold green]  ]"
        elif text[:3] in self.inner_bullets:
            _len = 3
            is_bullet = True
            if not color:
                if text[:3] == "#> ":
                    color = "pink"
                else:
                    color = "blue"
        elif text[:8].lower() == "warning:":
            _len = 8
            is_bullet = True
            if not color:
                color = "orange"
        elif text[:2] == "E:":
            _len = 2
            is_bullet = True
            if not color:
                color = "red"
        elif text[:2] in ["* "]:
            _len = 2
            is_bullet = True
            if not color:
                color = "blue"
        elif "SUCCESS" in text or "Finalazing" in text or text in ["END", "DONE"]:
            if not color:
                color = "green"
                is_bold = True
        elif text in ["FAILED", "ERROR"]:
            if not color:
                color = "red"

        return text, color, _len, is_bullet, is_r, is_bold


def br(text, color="white"):
    if color != "white":
        return f"[bold][[/bold][{color}]  {text}  [/{color}][bold]][/bold]"
    else:
        return f"[bold][[/bold]  {text}  [bold]][/bold]"


def ok():
    """Done."""
    return " [[g]ok[/g]]"


def _console_clear():
    console.clear()


def console_ruler(msg="", character="=", color="cyan", style="green", fn=""):
    """Draw console ruler.

    Indicate rich console to write into given fn
    __ https://stackoverflow.com/a/6826099/2402577
    """
    from broker import cfg

    if threading.current_thread().name != "MainThread" and cfg.IS_THREADING_ENABLED:
        fn = thread_log_files[threading.current_thread().name]
    elif not fn:
        if ll.LOG_FILENAME:
            fn = ll.LOG_FILENAME
        elif DRIVER_LOG:
            fn = DRIVER_LOG
        else:
            fn = "program.log"

    if fn not in ll.console:
        ll.console[fn] = Console(file=open(fn, "a"), force_terminal=True, theme=custom_theme)

    if msg:
        console.rule(f"[bold][{color}]{msg}", characters=character, style=style)
        ll.console[fn].rule(f"[bold][{color}]{msg}", characters=character, style=style)
    else:
        console.rule(characters=character, style=style)
        ll.console[fn].rule(characters=character, style=style)


def _log(text, color, is_bold, fn, end="\n", is_write=True, is_output=True, highlight=True):
    if not is_output:
        is_print = is_output
    else:
        is_print = ll.IS_PRINT

    if threading.current_thread().name != "MainThread":
        # prevent writing Thread's output onto console
        is_print = False

    text, _color, _len, is_bullet, is_r, is_bold = ll.pre_color_check(text, color, is_bold)
    if is_bold and not is_bullet:
        _text = f"[bold]{text}[/bold]"
    else:
        _text = text

    if end == "\r" and text:
        text = f"{text}"

    if color and color != "white":
        if is_print:
            if not IS_THREADING_MODE_PRINT or threading.current_thread().name == "MainThread":
                if is_bullet:
                    _msg = f"[bold][{_color}]{is_r}{text[:_len]}[/{_color}][/bold][{color}]{text[_len:]}[/{color}]"
                    console.print(_msg, end=end)
                else:
                    ll.print_color(str(text), color, is_bold=is_bold, highlight=highlight, end=end)

        if is_bold:
            _text = f"[bold]{text[_len:]}[\bold]"
        else:
            _text = text[_len:]

        _text = text[_len:]
        if is_write and IS_WRITE:
            if is_bullet:
                ll.console[fn].print(
                    f"[bold][{_color}]{is_r}{text[:_len]}[/{_color}][/bold][{color}]{_text}[/{color}]",
                    end=end,
                    soft_wrap=True,
                )
            else:
                if color:
                    ll.console[fn].print(f"[{color}]{_text}[/{color}]", end=end, highlight=highlight, soft_wrap=True)
                else:
                    ll.console[fn].print(_text, end=end, highlight=highlight, soft_wrap=True)
    else:
        text_to_write = ""
        if is_bullet:
            text_to_write = f"[bold][{_color}]{is_r}{_text[:_len]}[/{_color}][/bold]{_text[_len:]}"
        else:
            if _color:
                text_to_write = f"[{_color}]{_text}[/{_color}]"
            else:
                text_to_write = _text

        if is_print:
            console.print(text_to_write, highlight=highlight, end=end)

        if is_write and IS_WRITE:
            ll.console[fn].print(text_to_write, end=end, highlight=highlight, soft_wrap=True)


def log(
    text="",
    color=None,
    fn=None,
    is_write=True,
    is_code=False,
    is_wrap=False,
    is_err=False,
    is_output=True,
    max_depth=None,
    h=True,
    _ok=False,
    back=0,
    end="\n",
    width=120,
):
    """Log output with the own settings.

    * Emojis: python -m rich.emoji | less
    * Colors:
    __ https://rich.readthedocs.io/en/latest/appendix/colors.html#appendix-colors
    __ https://github.com/dracula/dracula-theme

    :param end: (str, optional) Character to write at end of output. Defaults to "\\n".
    :param text: String to print
    :param color: Color of the complete string
    :param fn: Filename to write
    :param h: Stands for highlight. Rich will highlight certain patterns in your output
        such as numbers, strings, and other objects like IP addresses. You can
        disable highlighting by setting highlight=False.
    """
    if isinstance(text, QuietExit):
        text = str(text)

    is_bold: bool = False
    if color in ["bold", "b"]:
        is_bold = True
        color = None

    if is_err:
        text = str(text)
        if text:
            if "E: " not in text[3] and "warning:" not in text.lower():
                text = f"E: {text}"
            elif "E: warning: " in text:
                text = f"E: {text.replace('E: warning: ', '')}"
        else:
            return

        text = text.replace("E: warning:", "warning:")

    if _ok:
        text = f"{text} {ok()}"

    if isinstance(text, str):
        if "E: " == text[:3]:
            text = f"{WHERE(back, bracket_c='red')}[alert] E:[/alert] {text[3:]}"
        elif "E: " in text[3:]:
            _text = text.replace("warning: ", "").replace("E: ", "")
            text = f"{WHERE(back)} {_text}"
            if "E: warning: " in text:
                text = f"{WHERE(back)}[orange] warning:[/orange] {_text}"
            else:
                if "warning:" in text:
                    text = f"{WHERE(back)}[orange] warning:[/orange] {_text}"
                else:
                    text = f"{WHERE(back)}[alert] E:[/alert] {_text}"

    if is_code:
        h = False
        base_str = ""
        if text[0:2] == "$ ":
            text = "[bg]$[/bg] " + text[2:]
            base_str = " \ \n      "
        else:
            base_str = " \ \n    "

        text = base_str.join(textwrap.wrap(text, width, break_long_words=False, break_on_hyphens=False))

    if is_wrap:
        text = "\n".join(textwrap.wrap(text, width, break_long_words=False, break_on_hyphens=False))

    if is_write and IS_WRITE:
        if threading.current_thread().name != "MainThread" and cfg.IS_THREADING_ENABLED:
            fn = thread_log_files[threading.current_thread().name]
        elif not fn:
            if ll.LOG_FILENAME:
                fn = ll.LOG_FILENAME
            elif DRIVER_LOG:
                fn = DRIVER_LOG
            else:
                fn = "program.log"

        if fn not in ll.console:
            #: Indicated rich console to write into given fn
            # __ https://stackoverflow.com/a/6826099/2402577
            ll.console[fn] = Console(file=open(fn, "a"), force_terminal=True, theme=custom_theme)

    if isinstance(text, list):
        pprint(text)
        if is_write and IS_WRITE:
            ll.console[fn].print(text)
    elif isinstance(text, dict):
        if max_depth:
            pprint(text, max_depth=max_depth)
        else:
            pprint(text)

        if is_write and IS_WRITE:
            ll.console[fn].print(text)
    else:
        _log(text, color, is_bold, fn, end, is_write, is_output, h)


def WHERE(back=0, bracket_c="green"):
    import os
    import sys

    """Return line number where the command is called."""
    try:
        frame = sys._getframe(back + 2)
    except:
        frame = sys._getframe(1)

    text = os.path.basename(frame.f_code.co_filename)
    return f"[{bracket_c}][[/{bracket_c}][blue]  {text}[/blue]:{frame.f_lineno}  [{bracket_c}]][/{bracket_c}]"


ll = Log()
