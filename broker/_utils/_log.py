#!/usr/bin/env python3

import os
import pathlib
import sys
import textwrap
import threading
from typing import Dict, Union

from rich import pretty, print, print_json  # noqa
from rich.console import Console
from rich.pretty import pprint
from rich.theme import Theme
from rich.traceback import install

from broker import cfg

install()  # for rich, show_locals=True
# pretty.install()

DRIVER_LOG = None
IS_THREADING_MODE_PRINT = False
thread_log_files: Dict[str, str] = {}
custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "magenta",
        "danger": "bold red",
        "b": "bold",
        "m": "magenta",
        # "magenta": "#ff79c6",
    }
)
console = Console(theme=custom_theme)


class Colors:
    red = "#ff5555"
    pink = "#ff79c6"


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

    def print_color(self, text: str, color=None, is_bold=True, end=None) -> None:
        """Print string in color format."""
        if text[0:3] in ["==>", "#> ", "## "]:
            if color and text == "==> ":
                print(f"[bold {color}]{text[0:3]}[/bold {color}]", end="", flush=True)
            else:
                print(f"[bold blue]{text[0:3]}[/bold blue]", end="", flush=True)

            text = text[3:]
        elif text[0:2] == "E:":
            print("[bold red]E:[/bold red]", end="", flush=True)
            text = text[2:]

        if end is None:
            if is_bold:
                print(f"[bold {color}]{text}[/bold {color}]")
            else:
                print(f"[{color}]{text}[/{color}]")
        else:
            if is_bold:
                print(f"[bold {color}]{text}[/bold {color}]", end="", flush=True)
            else:
                print(f"[{color}]{text}[/{color}]", end="")

    def pre_color_check(self, text, color, is_bold):
        """Check color for substring."""
        text = str(text)
        _len = None
        is_bullet = False
        is_r = ""
        if text and text[0] == "\r":
            is_r = "\r"
            text = text[1:]

        if text == "[ ok ]":
            text = "[  [bold green]OK[/bold green]  ]"
        elif text[:3] in ["==>", "#> ", "## ", " * ", "###", "** ", "***"]:
            _len = 3
            is_bullet = True
            if not color:
                color = "blue"
        elif text[:8].lower() == "warning:":
            _len = 8
            is_bullet = True
            if not color:
                color = "yellow"
        elif text[:2] == "E:":
            _len = 2
            is_bullet = True
            if not color:
                color = "red"
        elif "SUCCESS" in text or "Finalazing" in text or text in ["END", "FIN"]:
            if not color:
                color = "green"
                is_bold = True
        elif text in ["FAILED", "ERROR"]:
            if not color:
                color = "red"

        return text, color, _len, is_bullet, is_r, is_bold


def br(text, color="white"):
    if color != "white":
        return f"[bold][[/bold][{color}]{text}[/{color}][bold]][/bold]"
    else:
        return f"[bold][[/bold]{text}[bold]][/bold]"


def ok(text="OK"):
    if text == "OK":
        text = br(f"  [green]{text}[/green]  ")
        return f"  {text}"
    else:
        return br(f"  [green]{text}[/green]  ")


def _console_clear():
    console.clear()


def console_ruler(msg="", character="=", color="cyan", fn=""):
    """Draw console ruler.

    Indicated rich console to write into given fn
    __ https://stackoverflow.com/a/6826099/2402577
    """
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
        console.rule(f"[bold {color}]{msg}", characters=character)
        ll.console[fn].rule(f"[bold {color}]{msg}", characters=character)
    else:
        console.rule(characters=character)
        ll.console[fn].rule(characters=character)


def _log(text, color, is_bold, flush, fn, end, is_write=True, is_output=True):
    if not is_output:
        is_print = is_output
    else:
        is_print = ll.IS_PRINT

    if threading.current_thread().name != "MainThread":
        # prevent writing Thread's output into console
        is_print = False

    text, _color, _len, is_bullet, is_r, is_bold = ll.pre_color_check(text, color, is_bold)
    if is_bold and not is_bullet:
        _text = f"[bold]{text}[/bold]"
    else:
        _text = text

    if color:
        if is_print:
            if not IS_THREADING_MODE_PRINT or threading.current_thread().name == "MainThread":
                if is_bullet:
                    print(
                        f"[bold {_color}]{is_r}{text[:_len]}[/bold {_color}][{color}]{text[_len:]}[/{color}]",
                        end=end,
                        flush=flush,
                    )
                else:
                    ll.print_color(str(text), color, is_bold=is_bold, end=end)

        if is_bold:
            _text = f"[bold]{text[_len:]}[\bold]"
        else:
            _text = text[_len:]

        _text = text[_len:]
        if is_write:
            if is_bullet:
                ll.console[fn].print(
                    f"[bold {_color}]{is_r}{text[:_len]}[/bold {_color}][{color}]{_text}[/{color}]",
                    end=end,
                    soft_wrap=True,
                )
            else:
                if color:
                    ll.console[fn].print(f"[bold {color}]{_text}[/bold {color}]", end="", soft_wrap=True)
                else:
                    ll.console[fn].print(_text, end="", soft_wrap=True)
    else:
        text_write = ""
        if is_bullet:
            text_write = f"[bold {_color}]{is_r}{_text[:_len]}[/bold {_color}][bold]{_text[_len:]}[/bold]"
        else:
            if _color:
                text_write = f"[{_color}]{_text}[/{_color}]"
            else:
                text_write = _text

        if is_print:
            if end == "":
                print(text_write, end="")
            else:
                print(text_write, flush=flush)

        if is_write:
            ll.console[fn].print(text_write, end=end, soft_wrap=True)

    if end is None:
        if is_write:
            ll.console[fn].print("")

        if color and is_bullet:
            print()


def log(
    text="",
    color=None,
    fn=None,
    end=None,
    flush=False,
    is_write=True,
    where_back=0,
    is_code=False,
    is_align=False,
    is_err=False,
    is_output=True,
    max_depth=None,
):
    """Log output with own settings.

    * colors:
    __ https://rich.readthedocs.io/en/latest/appendix/colors.html#appendix-colors

    :param text: string to print
    :param color: color of the complete string
    :param fn: filename to write
    """
    is_bold: bool = False
    if color in ["bold", "b"]:
        is_bold = True
        color = None

    if is_err:
        text = str(text)
        if text:
            if "E: " not in text[3] and "warning:" not in text.lower():
                text = f"E: {text}"
        else:
            return

        text = text.replace("E: warning:", "warning:")

    if isinstance(text, str) and "E: " in text[3:]:
        _text = text.replace("warning: ", "").replace("E: ", "")
        if "E: warning: " not in text:
            if "warning:" in text:
                text = f"{WHERE(where_back)}[bold yellow] warning:[/bold yellow] [bold]{_text}"
            else:
                text = f"{WHERE(where_back)}[bold {c.red}] E:[/bold {c.red}] [bold]{_text}"
        else:
            text = f"{WHERE(where_back)}[bold yellow] warning:[/bold yellow] [bold]{_text}"

    if "-=-=" in str(text):
        is_bold = True

    if is_code:
        text = " \ \n  ".join(textwrap.wrap(text, 80, break_long_words=False, break_on_hyphens=False))

    if is_align:
        text = "\n".join(textwrap.wrap(text, 80, break_long_words=False, break_on_hyphens=False))

    if is_write:
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

    if isinstance(text, dict):
        if max_depth:
            pprint(text, max_depth=max_depth)
        else:
            pprint(text)

        if is_write:
            ll.console[fn].print(text)
    else:
        _log(text, color, is_bold, flush, fn, end, is_write, is_output)


def WHERE(back=0):
    """Return line number where the command is called."""
    try:
        frame = sys._getframe(back + 2)
    except:
        frame = sys._getframe(1)

    text = f"{os.path.basename(frame.f_code.co_filename)}[/bold blue]:{frame.f_lineno}"
    return f"[bold green][[/bold green][bold blue] {text} [bold green]][/bold green]"


ll = Log()
c = Colors()
