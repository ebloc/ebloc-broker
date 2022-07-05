#!/usr/bin/env python3

import logging
import threading
import time

from broker.config import IgnoreThreadsFilter, ThreadFilter

# Attach the IgnoreThreadsFilter to the main root log handler.
# This is responsible for ignoring all log records originating from
# new threads.
main_handler = logging.FileHandler("/tmp/mainlogfile.log", "a")
main_handler.addFilter(IgnoreThreadsFilter())

_log = logging.getLogger()  # root logger
for hdlr in _log.handlers[:]:  # remove all the old handlers
    _log.removeHandler(hdlr)

logging.basicConfig(
    # handlers=[main_handler],
    handlers=[logging.StreamHandler(), main_handler],
    level=logging.INFO,
    format="[%(asctime)s %(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger()
log.info("running example")


def hello(name):  # shared module on write time
    log.info(name)


def thread_function(name):
    # A dedicated per-thread handler
    # thread_file_handler = f"/tmp/threadlogfile-{threading.get_ident()}.log"
    thread_file_handler = f"/tmp/threadlogfile{name}.log"
    thread_handler = logging.FileHandler(thread_file_handler, "a")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    thread_handler.setFormatter(formatter)
    # The ThreadFilter makes sure this handler only accepts logrecords that originate
    # in *this* thread, only. It needs the current thread id for this:
    thread_handler.addFilter(ThreadFilter(thread_id=threading.get_ident()))
    log.addHandler(thread_handler)
    time.sleep(0.25)
    hello(name)


def main():
    log.info("main_thread_start")
    # consider giving the thread a name (add name=...), then you could
    # use ThreadFilter(threadname=...) to select on all messages with that name
    # The thread name does not have to be unique.
    x = threading.Thread(target=thread_function, args=("thread_1",))
    y = threading.Thread(target=thread_function, args=("thread_2",))
    x.start()
    y.start()
    hello("main_thread_end")


if __name__ == "__main__":
    main()
