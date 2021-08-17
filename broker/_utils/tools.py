#!/usr/bin/env python3

import decimal
import linecache
import os
import sys
import threading
import time
import traceback
from datetime import datetime
from decimal import Decimal

import pytz
from colorama import init
from pygments import formatters, highlight, lexers
from pytz import timezone
from rich.traceback import install
from termcolor import colored

import broker._config as _config
from broker.config import QuietExit, env

install()  # for rich
init(autoreset=True)  # for colorama

log_files = {}


class Color:
    def __init__(self):
        """
        Color class.

        Available text colors:
        red, green, yellow, blue, magenta, cyan, white.

        Available text highlights:
        on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white.

        Available attributes:
        bold, dark, underline, blink, reverse, concealed.

        Example:
        colored('Hello, World!', 'red', 'on_grey', ['blue', 'blink'])
        colored('Hello, World!', 'green')
        """
        self.BOLD = "\033[1m"
        self.END = "\033[0m"
        #
        self.red = "red"
        self.green = "green"
        self.yellow = "yellow"
        self.blue = "blue"
        self.magenta = "magenta"
        self.cyan = "cyan"
        self.white = "white"
        # self.DEFAULT = "\033[99m"
        # self.PURPLE = "\033[95m"
        # self.BLUE = "\033[94m"
        # self.RED = "\033[91m"
        # self.GREY = "\033[90m"
        # self.YELLOW = "\033[93m"
        # self.BLACK = "\033[90m"
        # self.CYAN = "\033[96m"
        # self.GREEN = "\033[92m"
        # self.MAGENTA = "\033[95m"
        # self.WHITE = "'\033[97m"


class Log(Color):
    """Color class."""

    def __init__(self):  # noqa
        super().__init__()

    def print_color(self, text, color=None, is_bold=True, end=None):
        """Print string in color format."""
        if str(text)[0:3] in ["==>", "#> ", "## "]:
            print(colored(f"{self.BOLD}{str(text)[0:3]}{self.END}", "blue"), end="", flush=True)
            text = text[3:]
        elif str(text)[0:2] == "E:":
            print(colored(f"{self.BOLD}E:{self.END}", "red"), end="", flush=True)
            text = text[2:]

        if end is None:
            if is_bold:
                print(colored(f"{self.BOLD}{text}{self.END}", color))
            else:
                print(colored(text, color))
        elif end == "":
            if is_bold:
                print(colored(f"{self.BOLD}{text}{self.END}", color), end="", flush=True)
            else:
                print(colored(text, color), end="")

    def pre_color_check(self, text, color, is_bold):
        """Check color for substring."""
        text = str(text)
        _len = None
        is_arrow = False
        if text == "[ ok ]":
            text = f"[ {ll.green}ok{ll.END} ]"

        if not color:
            if text[:3] in ["==>", "#> ", "## ", " * ", "###"]:
                _len = 3
                is_arrow = True
                color = ll.blue
            elif text[:8] in ["Warning:", "warning:"]:
                _len = 8
                is_arrow = True
                color = ll.yellow
            elif text[:2] == "E:":
                _len = 2
                is_arrow = True
                color = ll.red
            elif "SUCCESS" in text or "Finalazing..." in text:
                color = ll.green
            elif text in ["FAILED", "ERROR"]:
                color = ll.red
            elif is_bold:
                color = ll.white

        return text, color, _len, is_arrow


ll = Log()


def WHERE(back=0):
    try:
        frame = sys._getframe(back + 2)
    except:
        frame = sys._getframe(1)

    return f"{os.path.basename(frame.f_code.co_filename)}:{frame.f_lineno}"


def unix_time_millis(dt) -> int:
    unix_timestamp = dt.timestamp()
    return int(unix_timestamp * 1000)


def _timestamp(zone="Europe/Istanbul") -> int:
    """Return timestamp of now."""
    return int(time.mktime(datetime.now(timezone(zone)).timetuple()))


def _time(zone="Europe/Istanbul"):
    return datetime.now(timezone(zone)).strftime("%Y-%m-%d %H:%M:%S")


def get_dt_time(zone="Europe/Istanbul"):
    """Return datetime object."""
    return datetime.now(timezone(zone))


def timestamp_to_local(posix_time: int, zone="Europe/Istanbul"):
    """Return date in %Y-%m-%d %H:%M:%S format."""
    ts = posix_time / 1000.0
    tz = pytz.timezone(zone)
    return datetime.fromtimestamp(ts, tz).strftime("%Y-%m-%d %H:%M:%S")


def utc_to_local(utc_dt, zone="Europe/Istanbul"):
    # dt.strftime("%d/%m/%Y") # to get the date
    local_tz = pytz.timezone(zone)
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    return '{}:{} "{}"'.format(os.path.basename(filename), lineno, line.strip())


def _colorize_traceback(message=None, is_print_exc=True):
    """Log the traceback."""
    if isinstance(message, QuietExit):
        if message:
            log(message)
        return True

    if isinstance(message, BaseException):
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(message).__name__, message.args)

    tb_text = "".join(traceback.format_exc())
    lexer = lexers.get_lexer_by_name("pytb", stripall=True)
    # to check: print $terminfo[colors]
    formatter = formatters.get_formatter_by_name("terminal")
    tb_colored = highlight(tb_text, lexer, formatter)
    if not message:
        log(f"{WHERE(1)} ", "blue")
    else:
        try:
            log(f"[{PrintException()}] WHERE={WHERE(1)}", "blue")
        except:
            log(f"WHERE={WHERE(1)}", "blue")

        log(f"E: {message}")

    if is_print_exc:
        _tb_colored = tb_colored.rstrip()
        if _tb_colored and _tb_colored != "NoneType: None":
            log(_tb_colored)


def log(text="", color=None, filename=None, end=None, is_bold=True, flush=False):
    """Print for own settings."""
    text, _color, _len, is_arrow = ll.pre_color_check(text, color, is_bold)
    if threading.current_thread().name != "MainThread" and env and env.IS_THREADING_ENABLED:
        filename = log_files[threading.current_thread().name]
    elif not filename:
        try:
            if env:
                if env.log_filename:
                    filename = env.log_filename
                else:
                    filename = env.DRIVER_LOG

            if filename is None:
                filename = "program.log"
            elif not os.path.isfile(filename):
                filename = "program.log"
        except:
            filename = "program.log"

    if is_bold:
        _text = f"{ll.BOLD}{text}{ll.END}"
    else:
        _text = text

    f = open(filename, "a")
    if color:
        if not _config.IS_THREADING_MODE_PRINT or threading.current_thread().name == "MainThread":
            if is_arrow:
                print(
                    colored(f"{ll.BOLD}{text[:_len]}{ll.END}", _color) + f"{ll.BOLD}{text[_len:]}{ll.END}",
                    end=end,
                    flush=flush,
                )
            else:
                ll.print_color(colored(text, color), color, is_bold=is_bold, end=end)

        if is_bold:
            _text = f"{ll.BOLD}{text[_len:]}{ll.END}"
        else:
            _text = text[_len:]

        if is_arrow:
            f.write(colored(f"{ll.BOLD}{text[:_len]}{ll.END}", _color) + colored(_text, color))
        else:
            f.write(colored(_text, color))
    else:
        text_write = ""
        if is_arrow:
            text_write = colored(f"{ll.BOLD}{text[:_len]}{ll.END}", _color) + f"{ll.BOLD}{text[_len:]}{ll.END}"
        else:
            text_write = text

        print(text_write, end=end, flush=flush)
        f.write(text_write)

    if end is None:
        f.write("\n")

    f.close()


def get_decimal_count(value, is_drop_trailing_zeros=True) -> int:
    """Return decimal count.

    https://stackoverflow.com/a/6190291/2402577

    See https://stackoverflow.com/a/11227878/2402577
    for drop the trailing zeros from decimal.
    """
    value = str(value)
    if is_drop_trailing_zeros:
        value = str(value.rstrip("0").rstrip(".") if "." in value else value)

    d = decimal.Decimal(str(value))
    return abs(d.as_tuple().exponent)


def round_float(v, ndigits=2) -> float:
    """Limit floats to two decimal points.

    https://stackoverflow.com/questions/455612/limiting-floats-to-two-decimal-points
    """
    d = Decimal(v)
    v_str = (f"{{0:.{ndigits}f}}").format(round(d, ndigits))  # '{0:.8f}'
    return float(v_str)
