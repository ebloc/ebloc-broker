#!/usr/bin/env python3

import decimal
import linecache
import os
import signal
import sys
import time
import traceback
from contextlib import suppress
from datetime import datetime
from decimal import Decimal

# from os import listdir
from subprocess import PIPE, CalledProcessError, Popen, check_output

from pytz import timezone, utc

try:
    from broker._utils._log import br
except:  # if ebloc_broker used as a submodule
    from ebloc_broker.broker._utils._log import br

try:
    from broker._utils._log import log
except:  # if ebloc_broker used as a submodule
    from ebloc_broker.broker._utils._log import log


class HandlerException(Exception):
    """Generate HandlerException."""


class JobException(Exception):
    """Trace is not printed."""

class QuietExit(Exception):
    """Trace is not printed."""


def WHERE(back=0):
    """Return line number where the command is called."""
    try:
        frame = sys._getframe(back + 2)
    except:
        frame = sys._getframe(1)

    text = f"{os.path.basename(frame.f_code.co_filename)}[/bold blue]:{frame.f_lineno}"
    return f"[bold green][[/bold green][bold blue]{text}[bold green]][/bold green]"


def merge_two_dicts(x, y):
    """Given two dictionaries, merge them into a new dict as a shallow copy.

    __https://stackoverflow.com/a/26853961/2402577
    """
    z = x.copy()
    z.update(y)
    return z


def timenow() -> int:
    """Return UTC timestamp."""
    d = datetime.utcnow()
    print(d)
    epoch = datetime(1970, 1, 1)
    return int((d - epoch).total_seconds())


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
    tz = timezone(zone)
    return datetime.fromtimestamp(ts, tz).strftime("%Y-%m-%d %H:%M:%S")


def utc_to_local(utc_dt, zone="Europe/Istanbul"):
    # dt.strftime("%d/%m/%Y") # to get the date
    local_tz = timezone(zone)
    local_dt = utc_dt.replace(tzinfo=utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    return '{}:{} "{}"'.format(os.path.basename(filename), lineno, line.strip())


def print_tb(message=None, is_print_exc=True) -> None:
    """Log the traceback."""
    if isinstance(message, QuietExit):
        if str(message):
            log(message, "bold")

        return

    if isinstance(message, BaseException):
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(message).__name__, message.args)

    tb_text = "".join(traceback.format_exc())
    if is_print_exc and tb_text != "NoneType: None\n":
        log(tb_text, "bold")

    # console.print_exception()  #arg: show_locals=True
    if not message:
        log(f"{WHERE(1)} ", "bold blue")
    else:
        with suppress(Exception):
            log(f"{br(PrintException())} ", "bold blue", end="")

        log(f"{WHERE(1)}", "bold blue")
        if "An exception of type CalledProcessError occurred" not in message:
            if "Warning:" not in message:
                log(f"E: {message}")
            else:
                log(message)


def delete_last_line(n=1):
    """Delete the last line in the STDOUT."""
    for _ in range(n):
        sys.stdout.write("\x1b[1A")  # cursor up one line
        sys.stdout.write("\x1b[2K")  # delete last line


def decimal_count(value, is_drop_trailing_zeros=True) -> int:
    """Return decimal count.

    See https://stackoverflow.com/a/11227878/2402577
    for drop the trailing zeros from decimal.

    __ https://stackoverflow.com/a/6190291/2402577
    """
    value = str(value)
    if is_drop_trailing_zeros:
        value = str(value.rstrip("0").rstrip(".") if "." in value else value)

    d = decimal.Decimal(str(value))
    return abs(d.as_tuple().exponent)


def round_float(v, ndigits=2) -> float:
    """Limit floats to two decimal points.

    __ https://stackoverflow.com/questions/455612/limiting-floats-to-two-decimal-points
    """
    d = Decimal(v)
    v_str = (f"{{0:.{ndigits}f}}").format(round(d, ndigits))
    return float(v_str)


def _exit(msg):
    """Immediate program termination."""
    log(msg)
    log("## Exiting")
    os._exit(0)


def _percent_change(initial: float, final=None, change=None, decimal: int = 2):
    try:
        initial = float(initial)
        if final:
            final = float(final)
        if change:
            change = float(change)
    except ValueError:
        return None

    if change is not None:
        try:
            initial = abs(initial)
            return round(change / abs(initial) * 100, decimal)
        except:
            return 0.0
    else:
        try:
            change = final - initial
            return round(change / abs(initial) * 100, decimal)
        except:
            return 0.0


def percent_change(initial, change, _decimal=8, end=None, is_arrow_print=True):
    """Calculate percent change."""
    try:
        initial = float(initial)
        change = float(change)
    except ValueError:
        return None

    change = "{0:.8f}".format(float(change))
    # percent = round((float(change)) / abs(float(initial)) * 100, 8)
    percent = _percent_change(initial=initial, change=change, decimal=_decimal)
    if percent == -0.0:
        change = 0.0
        color = "white"
    elif percent > 0:
        color = "green"
    else:
        color = "red"

    if abs(float(change)) < 0.1:
        change = "{0:.8f}".format(float(change))
    else:
        change = "{0:.2f}".format(float(change))

    if is_arrow_print:
        log(f"{format(initial, '.4f')} => ", end="")
        log(f"{format(float(initial) + float(change), '.4f')} ", "blue", end="")

    if float(change) >= 0:
        change = " " + change

    if is_arrow_print:
        log(f"{change}({format(float(percent), '.2f')}%) ", color, end=end)
    else:
        log(f"({format(float(percent), '.2f')}%) ", color, end=end)

    return percent


def print_trace(cmd, back=1, exc="", returncode=""):
    _cmd = " ".join(cmd)
    if exc:
        log(f"{WHERE(back)} CalledProcessError: returned non-zero exit status {returncode}", "red")
        log(f"[yellow]Command: [/yellow][white]{_cmd}", "bold")
        log(exc.rstrip(), "bold red")
    else:
        if returncode:
            return_code_msg = f"returned non-zero exit status {returncode}"
            log(f"E: Failed shell command {br(return_code_msg)}:\n[yellow]{_cmd}")
        else:
            log(f"E: Failed shell command:\n[yellow]{_cmd}")


def run(cmd, my_env=None) -> str:
    if not isinstance(cmd, str):
        cmd = list(map(str, cmd))  # all items should be str
    else:
        cmd = [cmd]

    try:
        if my_env is None:
            return check_output(cmd).decode("utf-8").strip()
        else:
            return check_output(cmd, env=my_env).decode("utf-8").strip()
    except CalledProcessError as e:
        print_trace(cmd, back=2, exc=e.output.decode("utf-8"), returncode=e.returncode)
        raise Exception from None
    except Exception as e:
        raise e


def is_process_on(process_name, name, process_count=0, port=None, is_print=True) -> bool:
    """Check wheather the process runs on the background.

    https://stackoverflow.com/a/6482230/2402577
    """
    p1 = Popen(["ps", "auxww"], stdout=PIPE)
    p2 = Popen(["grep", "-v", "-e", "flycheck_", "-e", "grep", "-e", "emacsclient"], stdin=p1.stdout, stdout=PIPE)
    p1.stdout.close()  # noqa
    p3 = Popen(["grep", "-E", process_name], stdin=p2.stdout, stdout=PIPE)
    p2.stdout.close()  # type: ignore
    output = p3.communicate()[0].decode("utf-8").strip().splitlines()
    pids = []
    for line in output:
        fields = line.strip().split()
        # Array indices start at 0 unlike awk, 1 indice points the port number
        pids.append(fields[1])

    if len(pids) > process_count:
        if port:
            # How to find processes based on port and kill them all?
            # https://stackoverflow.com/a/5043907/2402577
            p1 = Popen(["lsof", "-i", f"tcp:{port}"], stdout=PIPE)
            p2 = Popen(["grep", "LISTEN"], stdin=p1.stdout, stdout=PIPE)
            out = p2.communicate()[0].decode("utf-8").strip()
            running_pid = out.strip().split()[1]
            if running_pid in pids:
                if is_print:
                    log(f"==> {name} is already running on the background, its pid={running_pid}")

                return True
        else:
            if is_print:
                log(f"==> {name} is already running on the background")

            return True

    name = name.replace("\\", "").replace(">", "").replace("<", "")
    if is_print:
        print_tb(f"Warning: [green]{name}[/green] is not running on the background. {WHERE(1)}")

    return False


def mkdir(path) -> None:
    if not os.path.isdir(path):
        os.makedirs(path)


def mkdirs(paths) -> None:
    for path in paths:
        mkdir(path)


def kill_process_by_name(process_name):
    p1 = Popen(["ps", "auxww"], stdout=PIPE)
    p2 = Popen(["grep", "-E", process_name], stdin=p1.stdout, stdout=PIPE)
    p1.stdout.close()  # noqa
    p3 = Popen(["awk", "{print $2}"], stdin=p2.stdout, stdout=PIPE)
    p2.stdout.close()
    output = p3.communicate()[0].decode("utf-8").strip()
    lines = output.splitlines()
    for pid in lines:
        if pid.isnumeric():
            os.kill(int(pid), signal.SIGKILL)


def handler(signum, frame):
    """Register an handler for the timeout.

    __ https://docs.python.org/3/library/signal.html#example
    """
    if any(x in str(frame) for x in ["subprocess.py", "ssl.py", "log_job", "connection.py"]):
        # Signal handler called with signal=14 <frame at 0x7f9f3d4ff840, file
        # '/broker/eblocbroker/log_job.py', line 28, code log_loop>
        pass
    else:
        print_tb(f"E: Signal handler called with signum={signum} frame={frame}")
        raise HandlerException("Forever is over, end of time")


def bytes_to_mb(B) -> float:
    """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
    B = float(B)
    KB = float(1024)
    MB = float(KB ** 2)  # 1,048,576
    return float("{0:.5f}".format(B / MB))
