#!/usr/bin/env python3

import os
import pathlib
import sys
import textwrap
import threading
from typing import Dict, Union

from rich import pretty, print_json  # noqa # print
from rich.console import Console
from rich.pretty import pprint
from rich.theme import Theme
from rich.traceback import install

from broker import cfg
from broker.errors import QuietExit

install()  # for rich, show_locals=True
# pretty.install()

IS_WRITE = True  # if False disable write into file for the process
DRIVER_LOG = None
IS_THREADING_MODE_PRINT = False
thread_log_files: Dict[str, str] = {}
custom_theme = Theme(
    {
        "info": "bold magenta",  # "bold dim magenta"
        "alert": "bold red",
        "danger": "bold red",
        "bg": "bold green",
        "b": "bold",
        "m": "magenta",
        "w": "white",
        "cy": "cyan",
        "y": "yellow",
        "g": "green",
        "yob": "yellow on black blink",
    }
)
console = Console(
    theme=custom_theme,
    force_terminal=True,  # https://rich.readthedocs.io/en/latest/console.html#terminal-detection
    # force_interactive=False,
)


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
        self.inner_bullet_three = ["==>", "#> ", "## ", " * ", "###", "** ", "***", " **"]

    # def halo_decorator(self):
    #     with Halo(text="Loading", spinner="line", placement="right"):
    #         time.sleep(6)

    # def success() -> None:
    #     pass

    def print_color(self, text: str, color=None, is_bold=True, end="\n") -> None:
        """Print string in color format."""
        if text[0:3] in self.inner_bullet_three:
            if color and text == "==> ":
                console.print(f"[bold][{color}]{text[0:3]}[{color}][/bold]", end="")
            else:
                console.print(f"[bold blue]{text[0:3]}[/bold blue]", end="")

            text = text[3:]
        elif text[0:2] == "E:":
            console.print("[bold red]E:[/bold red]", end="")
            text = text[2:]

        if is_bold:
            console.print(f"[bold][{color}]{text}[{color}][/bold]", end=end)
        else:
            if color in ("white", "", None) and "[" not in text:
                print(text, end=end)
            else:
                console.print(f"[{color}]{text}[/{color}]", end=end)

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
        elif text[:3] in self.inner_bullet_three:
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
        return f"[bold][[/bold][{color}]{text}[/{color}][bold]][/bold]"
    else:
        return f"[bold][[/bold]{text}[bold]][/bold]"


def ok(text="OK"):
    if text == "OK":
        return "  " + br(f"  [green]{text}[/green]  ")
    else:
        return br(f"  [green]{text}[/green]  ")


def _console_clear():
    console.clear()


def console_ruler(msg="", character="=", color="cyan", fn=""):
    """Draw console ruler.

    Indicate rich console to write into given fn
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
        console.rule(f"[bold][{color}]{msg}", characters=character)
        ll.console[fn].rule(f"[bold][{color}]{msg}", characters=character)
    else:
        console.rule(characters=character)
        ll.console[fn].rule(characters=character)


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

    if color and color != "white":
        if is_print:
            if not IS_THREADING_MODE_PRINT or threading.current_thread().name == "MainThread":
                if is_bullet:
                    _msg = f"[bold][{_color}]{is_r}{text[:_len]}[/{_color}][/bold][{color}]{text[_len:]}[/{color}]"
                    console.print(_msg, end=end)
                else:
                    ll.print_color(str(text), color, is_bold=is_bold, end=end)

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
                    ll.console[fn].print(f"[{color}]{_text}[/{color}]", end=end, soft_wrap=True)
                else:
                    ll.console[fn].print(_text, end=end, soft_wrap=True)
    else:
        text_to_write = ""
        if is_bullet:
            text_to_write = f"[bold][{_color}]{is_r}{_text[:_len]}[/{_color}][/bold][bold]{_text[_len:]}[/bold]"
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
    highlight=True,
    success=False,
    back=0,
    end="\n",
):
    """Log output with the own settings.

    * Emojis: python -m rich.emoji | less
    * Colors:
    __ https://rich.readthedocs.io/en/latest/appendix/colors.html#appendix-colors

    :param end: (str, optional) Character to write at end of output. Defaults to "\\n".
    :param text: String to print
    :param color: Color of the complete string
    :param fn: Filename to write
    :param highlight: Rich will highlight certain patterns in your output such
        as numbers, strings, and other objects like IP addresses. You can
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

    if success:
        text = f"{text} {ok()}"

    if isinstance(text, str) and "E: " in text[3:]:
        _text = text.replace("warning: ", "").replace("E: ", "")
        if "E: warning: " in text:
            text = f"{WHERE(back)}[bold yellow] warning:[/bold yellow] [bold]{_text}"
        else:
            if "warning:" in text:
                text = f"{WHERE(back)}[bold yellow] warning:[/bold yellow] [bold]{_text}"
            else:
                text = f"{WHERE(back)}[bold red] E:[/bold red] [bold]{_text}"

    if "-=-=" in str(text):
        is_bold = True

    if is_code:
        base_str = ""
        if text[0:2] == "$ ":
            # is_bold = False
            base_str = " \ \n      "
        else:
            base_str = " \ \n    "

        text = base_str.join(textwrap.wrap(text, 120, break_long_words=False, break_on_hyphens=False))

    if is_wrap:
        text = "\n".join(textwrap.wrap(text, 80, break_long_words=False, break_on_hyphens=False))

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
        _log(text, color, is_bold, fn, end, is_write, is_output, highlight)


def WHERE(back=0):
    """Return line number where the command is called."""
    try:
        frame = sys._getframe(back + 2)
    except:
        frame = sys._getframe(1)

    text = os.path.basename(frame.f_code.co_filename)
    return f"[bold][green][[/green][blue]  {text}[/blue]:{frame.f_lineno}  [green]][/green][/bold]"


ll = Log()
