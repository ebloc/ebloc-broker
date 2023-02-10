#!/usr/bin/env python3

import decimal
import errno
import json
import linecache
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback
from contextlib import suppress
from datetime import datetime
from decimal import Decimal
from pathlib import PosixPath
from subprocess import PIPE, CalledProcessError, Popen, check_output

import requests
from pytz import timezone, utc

from broker._utils._log import WHERE, br, log, ok
from broker.errors import HandlerException, QuietExit, Terminate

try:
    import thread
except ImportError:
    import _thread as thread  # noqa


def merge_two_dicts(x, y):
    """Given two dictionaries, merge them into a new dict as a shallow copy.

    __https://stackoverflow.com/a/26853961/2402577
    """
    z = x.copy()
    z.update(y)
    return z


def timenow() -> int:
    """Return UTC timestamp."""
    dt = datetime.utcnow()
    log(f"UTC_now={dt.strftime('%Y-%m-%d %H:%M:%S')}", "bold")
    epoch = datetime(1970, 1, 1)
    return int((dt - epoch).total_seconds())


def unix_time_millis(dt) -> int:
    unix_timestamp = dt.timestamp()
    return int(unix_timestamp * 1000)


def _timestamp(zone="Europe/Istanbul") -> int:
    """Return timestamp of now."""
    return int(time.mktime(datetime.now(timezone(zone)).timetuple()))


def _date(zone="Europe/Istanbul", _type="", _format=""):
    """Return latest time.

    Zone could be: "UTC"
    """
    if _format:
        return datetime.now(timezone(zone)).strftime(_format)
    elif _type:
        if _type == "year":
            return datetime.now(timezone(zone)).strftime("%Y-%m-%d")
        elif _type == "month-day":
            return datetime.now(timezone(zone)).strftime("%m-%d")
        elif _type == "hour":
            return datetime.now(timezone(zone)).strftime("%H:%M:%S")

    return datetime.now(timezone(zone)).strftime("%Y-%m-%d %H:%M:%S")


def get_dt_time(zone="Europe/Istanbul"):
    """Return datetime object."""
    return datetime.now(timezone(zone))


def timestamp_to_local(posix_time: int, zone="Europe/Istanbul"):
    """Return date in %Y-%m-%d %H:%M:%S format."""
    ts = posix_time / 1000
    tz = timezone(zone)
    return datetime.fromtimestamp(ts, tz).strftime("%Y-%m-%d %H:%M:%S")


def utc_to_local(utc_dt, zone="Europe/Istanbul"):
    # dt.strftime("%d/%m/%Y") # to get the date
    local_tz = timezone(zone)
    local_dt = utc_dt.replace(tzinfo=utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)


def PrintException() -> str:
    _, _, tb = sys.exc_info()  # returns: exc_type, exc_obj, tb
    f = tb.tb_frame
    lineno = tb.tb_lineno
    fn = f.f_code.co_filename
    linecache.checkcache(fn)
    line = linecache.getline(fn, lineno, f.f_globals)
    return '{}:{} "{}"'.format(os.path.basename(fn), lineno, line.strip())


def print_tb(message=None, is_print_exc=True) -> None:
    """Log the traceback."""
    if message:
        if isinstance(message, QuietExit):
            if str(message):
                log(message, "bold")

            return

        if isinstance(message, BaseException):
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(message).__name__, message.args)

    sep_terminate = "raise Terminate"
    tb_text = "".join(traceback.format_exc())
    if sep_terminate in tb_text:
        tb_text = tb_text.split(sep_terminate, 1)[0] + "raise [m]Terminate[/m]()"

    if is_print_exc and tb_text != "NoneType: None\n":
        log(tb_text.rstrip(), back=1)

    if message and "An exception of type Exception occurred" not in message:
        log(message, back=1)


def _remove(path: str, is_verbose=False) -> None:
    """Remove file or folders based on its type.

    __ https://stackoverflow.com/a/10840586/2402577
    """
    try:
        if path == "/":
            raise ValueError("E: Attempting to remove root(/)")

        if not path:
            raise ValueError("E: Attempting to empty Path()")

        if os.path.isfile(path):
            with suppress(FileNotFoundError):
                os.remove(path)
        elif os.path.isdir(path):
            # deletes a directory and all its contents
            shutil.rmtree(path)
        else:
            if is_verbose:
                log(f"warning: {WHERE(1)} Nothing removed, following path does not exist:\n[m]{path}")

            return

        if is_verbose:
            log(f"#> {WHERE(1)} following path:\n[m]{path}[/m] is removed")
    except OSError as e:
        # Suppress the exception if it is a file not found error.
        # Otherwise, re-raise the exception.
        if e.errno != errno.ENOENT:
            print_tb(e)
            raise e


def delete_multiple_lines(n=1):
    """Delete the last line in the STDOUT."""
    for _ in range(n):
        sys.stdout.write("\x1b[1A")  # cursor up one line
        sys.stdout.write("\x1b[2K")  # delete the last line


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


def _sys_exit(msg="") -> None:
    """Exit the parent process."""
    if msg:
        if msg[:2] != "E:":
            log(f"E: {msg}")
        else:
            log(msg)

    log(f"#> Exiting {_date()}[w]...")
    sys.exit()


def _exit(msg="") -> None:
    """Immediate program termination.

    os._exit() in Python is used to exit a process with a specified state
    without calling cleanup handlers, flushing stdio buffers, etc.

    Note.  This method is typically used in a child process after the os.fork()
    system call.  The standard way to exit a process is — this is the
    sys.exit(n) method.
    """
    if msg:
        if msg[:2] != "E:":
            log(f"E: {msg}")
        else:
            log(msg)

        log("#> exiting")

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


def percent_change(initial, change, _decimal=8, end=None, is_arrow=True, color=None, is_sign=True, is_print=True):
    """Calculate the changed percent."""
    if change == 0:
        log("warning: percent_change() <change> is given as 0")
        return 0

    if initial == 0:
        raise Exception("warning: <initial> is given as 0")

    try:
        initial = float(initial)
        change = format(float(change), ".8f")
    except ValueError as e:
        raise e

    percent = _percent_change(initial=initial, change=change, decimal=_decimal)
    if not is_print:
        return percent

    if abs(percent) == 0:
        change = 0.0
        if not color:
            color = "white"
    elif percent > 0:
        if not color:
            color = "green"
    elif not color:
        color = "red"

    if abs(float(change)) < 0.1:
        change = format(float(change), ".8f")
    else:
        change = format(float(change), ".2f")

    if is_arrow:
        log(f"{format(initial, '.4f')} => ", end="")
        log(f"{format(float(initial) + float(change), '.4f')} ", "blue", end="")

    if float(change) >= 0:
        change = " " + change

    if is_arrow:
        if is_sign:
            log(f"{change}({format(float(percent), '.2f')}%) ", color, end=end)
        else:
            log(f"{abs(change)}({format(float(abs(percent)), '.2f')}%) ", color, end=end)
    else:
        if is_sign:
            log(f"({format(float(percent), '.2f')}%) ", color, end=end)
        else:
            log(f"({format(float(abs(percent)), '.2f')}%) ", color, end=end)

    return percent


def print_trace(cmd, back=1, exc="", returncode="") -> None:
    if not isinstance(cmd, str):
        cmd = " ".join(cmd)

    if exc:
        log(f"{WHERE(back)} CalledProcessError: returned non-zero exit status {returncode}", "bold red")
        log(f"[blue]$ [/blue][white]{cmd}", "bold")
        log(exc.rstrip(), "bold red")
    else:
        if returncode:
            return_code_msg = f"returned non-zero exit status {returncode}"
            log(f"E: Failed command {br(return_code_msg)}:")
        else:
            log("E: Failed command:")

        log(cmd, "bold yellow", is_code=True)


def pre_cmd_set(cmd):
    if isinstance(cmd, str):
        return [cmd]
    else:
        if isinstance(cmd, PosixPath):
            return str(cmd)
        else:
            return list(map(str, cmd))  # all items should be string


def run(cmd, env=None, is_quiet=False, suppress_stderr=False) -> str:
    cmd = pre_cmd_set(cmd)
    try:
        if env is None:
            if suppress_stderr:
                return check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8").strip()
            else:
                return check_output(cmd).decode("utf-8").strip()
        else:
            return check_output(cmd, env=env).decode("utf-8").strip()
    except CalledProcessError as e:
        if not is_quiet:
            print_trace(cmd, back=2, exc=e.output.decode("utf-8"), returncode=e.returncode)

        # prevent tree of trace
        raise Exception from None
    except Exception as e:
        raise e


def constantly_print_popen(cmd):
    """Constantly print Popen output while script is running.

    __ https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
    """
    cmd = pre_cmd_set(cmd)
    ret = ""
    with Popen(cmd, stdout=PIPE, bufsize=1, universal_newlines=True) as p:
        for line in p.stdout:
            ret += line.strip()
            print(line, end="")  # process line here

        return ret

    if p.returncode != 0:
        raise CalledProcessError(p.returncode, p.args)


def is_process_on(process_name, name="", process_count=0, port=None, is_print=True) -> bool:
    """Check whether the process runs on the background.

    __ https://stackoverflow.com/a/6482230/2402577
    """
    if not name:
        name = process_name

    p1 = Popen(["ps", "auxww"], stdout=PIPE)
    p2 = Popen(["grep", "-v", "-e", "flycheck_", "-e", "grep", "-e", "emacsclient"], stdin=p1.stdout, stdout=PIPE)
    p1.stdout.close()  # type: ignore
    p3 = Popen(["grep", "-E", process_name], stdin=p2.stdout, stdout=PIPE)
    p2.stdout.close()  # type: ignore
    output = p3.communicate()[0].decode("utf-8").strip().splitlines()
    pids = []
    for line in output:
        fields = line.strip().split()
        # array indices start at 0 unlike awk, 1 indice points the port number
        pids.append(fields[1])

    if len(pids) > process_count:
        if port:
            # How to find processes based on port and kill them all?
            # https://stackoverflow.com/a/5043907/2402577
            p1 = Popen(["lsof", "-i", f"tcp:{port}"], stdout=PIPE)
            p2 = Popen(["grep", "LISTEN"], stdin=p1.stdout, stdout=PIPE)
            out = p2.communicate()[0].decode("utf-8").strip()
            pid = out.strip().split()[1]
            if pid in pids:
                if is_print:
                    log(f"==> [green]{name}[/green] is already running on the background, its pid={pid}")

                return True
        else:
            if is_print:
                log(f"==> [green]{name}[/green] is already running on the background")

            return True

    name = name.replace("\\", "").replace(">", "").replace("<", "")
    if is_print:
        print_tb(f"[bold green]{name}[/bold green] is not running on the background  {WHERE(1)}")

    return False


def mkdir(path) -> None:
    if not os.path.isdir(path):
        os.makedirs(path)


def mkdirs(paths) -> None:
    for path in paths:
        mkdir(path)


def kill_process_by_name(process_name: str) -> None:
    p1 = Popen(["ps", "auxww"], stdout=PIPE)
    p2 = Popen(["grep", "-E", process_name], stdin=p1.stdout, stdout=PIPE)
    p1.stdout.close()  # type: ignore
    p3 = Popen(["awk", "{print $2}"], stdin=p2.stdout, stdout=PIPE)
    p2.stdout.close()  # noqa
    output = p3.communicate()[0].decode("utf-8").strip()
    lines = output.splitlines()
    for pid in lines:
        if pid.isnumeric():
            os.kill(int(pid), signal.SIGKILL)


def bytes_to_mb(B) -> float:
    """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
    B = float(B)
    KB = float(1024)
    MB = float(KB**2)  # 1,048,576
    return float("{0:.5f}".format(B / MB))


def without_keys(d, keys):
    """Return dict without the given keys.

    __ https://stackoverflow.com/a/31434038/2402577
    """
    return {x: d[x] for x in d if x not in keys}


def quit_function(fn_name) -> None:
    print("\nwarning: ", end="")
    print("{0} took too long".format(fn_name), file=sys.stderr)
    # breakpoint()  # DEBUG
    sys.stderr.flush()  # python 3 stderr is likely buffered.
    thread.interrupt_main()  # raises KeyboardInterrupt


def exit_after(s):
    """Use as decorator to exit process if function takes longer than s seconds."""

    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, quit_function, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result

        return inner

    return outer


def read_json(path, is_dict=True):
    if os.path.isfile(path) and os.path.getsize(path) == 0:
        raise Exception("File size is empty")

    with open(path) as json_file:
        data = json.load(json_file)
        if is_dict:
            if isinstance(data, dict):
                return data
            else:
                return {}
        else:
            return data


def remove_trailing_zeros(number):
    return ("%f" % float(number)).rstrip("0").rstrip(".")


def handler(signum, frame):
    """Register an handler for the timeout.

    Example error: Signal handler called with signum=14 frame=<frame at
    0x7f2fb1cece40, file '/usr/lib/python3.8/threading.py', line 1027

    __  https://docs.python.org/3/library/signal.html#example
    """
    if any(
        x in str(frame) for x in ["subprocess.py", "ssl.py", "log_job", "connection.py", "threading.py", "utils.py"]
    ):
        pass
    else:
        log(f"E: Signal handler called with signum={signum} frame={frame}")
        traceback.print_stack()
        raise HandlerException("Forever is over, end of time")


def is_byte_str_zero(value: str) -> bool:
    if len(value) >= 2:
        if value[1] == "x":
            value = value.replace("x", "", 1)

    try:
        return not int(value)
    except:
        return False


def get_ip():
    endpoint = "https://ipinfo.io/json"
    response = requests.get(endpoint, verify=True)
    if response.status_code != 200:
        raise Exception(f"Status:{response.status_code}, problem with the request.")

    data = response.json()
    return data["ip"]


def countdown(seconds: int, is_verbose=False) -> None:
    if not is_verbose:
        log(f"## sleep_time={seconds} seconds                                             ")

    while seconds:
        mins, secs = divmod(seconds, 60)
        timer = "sleeping for {:02d}:{:02d}".format(mins, secs)
        print(f" * {_date()} | {timer}", end="\r")
        time.sleep(1)
        seconds -= 1


def squeue() -> None:
    try:
        squeue_output = run(["squeue"])
        if "squeue: error:" in str(squeue_output):
            raise Exception("squeue: error")
    except Exception as e:
        raise Terminate(
            "warning: SLURM is not running on the background. Please run:\nsudo ./broker/bash_scripts/run_slurm.sh"
        ) from e

    # Get real info under the header after the first line
    if len(f"{squeue_output}\n".split("\n", 1)[1]) > 0:
        # checks if the squeue output's line number is gretaer than 1
        log("view information about jobs located in the Slurm scheduling queue:", "bold yellow")
        log(f"{squeue_output}  {ok()}", "bold")


def compare_files(fn1, fn2) -> bool:
    """Compare to files.

    * If two files have the same content in Python:
    __ https://stackoverflow.com/a/1072576/2402577
    """
    with open(fn1, "r") as file1, open(fn2, "r") as file2:
        return file1.read() == file2.read()


def touch(fn) -> None:
    """Create empthy file, ex: touch fn."""
    open(fn, "a").close()


def pid_exists(pid):
    if pid < 0:
        return False  # NOTE: pid == 0 returns True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:  # errno.ESRCH
        return False  # No such process
    except PermissionError:  # errno.EPERM
        return True  # Operation not permitted (i.e., process exists)
    else:
        return True  # no error, we can send a signal to the process


def is_dir(path) -> bool:
    if not os.path.isdir(path):
        log(f"warning: {path} folder does not exist")
        return False

    return True


def remove_ansi_escape_sequence(string):
    """Remove the ANSI escape sequences from a string.

    __ https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
    """
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", string)
