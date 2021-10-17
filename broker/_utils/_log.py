#!/usr/bin/env python3

import pathlib
import threading
from typing import Dict, Union

from rich import pretty, print, print_json  # noqa
from rich.console import Console
from rich.pretty import pprint

# from rich.traceback import install
# install(show_locals=True)
# install()  # for rich
# pretty.install()


IS_THREADING_ENABLED = False
DRIVER_LOG = None
IS_THREADING_MODE_PRINT = False
thread_log_files: Dict[str, str] = {}


class Log:
    """Color class.

    Find colors from: python -m rich
    """

    def __init__(self):  # noqa
        super().__init__()
        self.IS_PRINT = True
        self.LOG_FILENAME: Union[str, pathlib.Path] = ""
        self.console: Dict[str, Console] = {}

    def print_color(self, text: str, color=None, is_bold=True, end=None) -> None:
        """Print string in color format."""
        if text[0:3] in ["==> ", "#> ", "## "]:
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
        else:  # end == "":
            if is_bold:
                print(f"[bold {color}]{text}[/bold {color}]", end="", flush=True)
            else:
                print(f"[{color}]{text}[/{color}]", end="")

    def pre_color_check(self, text, color, is_bold):
        """Check color for substring."""
        text = str(text)
        _len = None
        is_arrow = False
        is_r = ""
        if text and text[0] == "\r":
            is_r = "\r"
            text = text[1:]

        if text == "[ ok ]":
            text = "[ [bold green]ok[/bold green] ]"

        if text[:3] in ["==>", "#> ", "## ", " * ", "###"]:
            _len = 3
            is_arrow = True
            if not color:
                color = "blue"
        elif text[:8] in ["Warning:", "warning:"]:
            _len = 8
            is_arrow = True
            if not color:
                color = "yellow"
        elif text[:2] == "E:":
            _len = 2
            is_arrow = True
            if not color:
                color = "red"
        elif "SUCCESS" in text or "Finalazing" in text or text == "END":
            if not color:
                color = "green"
                is_bold = True
        elif text in ["FAILED", "ERROR"]:
            if not color:
                color = "red"

        return text, color, _len, is_arrow, is_r, is_bold


def br(text):
    return f"[bold][[/bold]{text}[bold]][/bold]"


def _log(text, color, is_bold, flush, filename, end):
    text, _color, _len, is_arrow, is_r, is_bold = ll.pre_color_check(text, color, is_bold)
    if is_bold and not is_arrow:
        _text = f"[bold]{text}[/bold]"
    else:
        _text = text

    if color:
        if ll.IS_PRINT:
            if not IS_THREADING_MODE_PRINT or threading.current_thread().name == "MainThread":
                if is_arrow:
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
        if is_arrow:
            ll.console[filename].print(
                f"[bold {_color}]{is_r}{text[:_len]}[/bold {_color}][{color}]{_text}[/{color}]",
                end=end,
                soft_wrap=True,
            )
        else:
            if color:
                ll.console[filename].print(f"[bold {color}]{_text}[/bold {color}]", end="", soft_wrap=True)
            else:
                ll.console[filename].print(_text, end="", soft_wrap=True)

    else:
        text_write = ""
        if is_arrow:
            text_write = f"[bold {_color}]{is_r}{_text[:_len]}[/bold {_color}][bold]{_text[_len:]}[/bold]"
        else:
            if _color:
                text_write = f"[{_color}]{_text}[/{_color}]"
            else:
                text_write = _text

        if ll.IS_PRINT:
            if end == "":
                print(text_write, end="")
            else:
                print(text_write, flush=flush)

        ll.console[filename].print(text_write, end=end, soft_wrap=True)

    if end is None:
        ll.console[filename].print("")
        if color and is_arrow:
            print()

    # f.close()


def log(text="", color=None, filename=None, end=None, flush=False):
    """Print for own settings.

    __ https://rich.readthedocs.io/en/latest/appendix/colors.html?highlight=colors
    """
    is_bold: bool = False
    if color == "bold":
        is_bold = True
        color = None

    if "-=-=" in str(text):
        is_bold = True

    if threading.current_thread().name != "MainThread" and IS_THREADING_ENABLED:
        filename = thread_log_files[threading.current_thread().name]
    elif not filename:
        if ll.LOG_FILENAME:
            filename = ll.LOG_FILENAME
        elif DRIVER_LOG:
            filename = DRIVER_LOG
        else:
            filename = "program.log"

    if filename not in ll.console:
        #: Indicated rich console to write into given filename
        # __ https://stackoverflow.com/a/6826099/2402577
        ll.console[filename] = Console(file=open(filename, "a"), force_terminal=True)

    if isinstance(text, dict):
        pprint(text)
        ll.console[filename].print(text)
    else:
        _log(text, color, is_bold, flush, filename, end)


ll = Log()
