#!/usr/bin/env python3

import errno
import os
import os.path
import time

import daemon.pidfile
import psutil

from config import env
from utils import popen_communicate


"""
- Python daemon no pidfile
  https://stackoverflow.com/a/23658292/2402577

- Python - python-daemon lockfile timeout on lock.aquire()
  https://stackoverflow.com/a/23665594/2402577
-
"""


class Daemon_base():
    def __init__(self, pidfile, working_directory, cmd):
        self.cmd = cmd
        self.pidfile = pidfile
        self.context = daemon.DaemonContext(
            working_directory=working_directory,
            pidfile=self.pidfile,
            umask=0o002  # u=rwx,g=rx,o=rx
        )

    class ProcessRunningException(BaseException):
        pass

    class DaemonRunnerError(Exception):
        """ Abstract base class for errors from DaemonRunner. """

        def __init__(self, *args, **kwargs):
            self._chain_from_context()
            super(self.DaemonRunnerError, self).__init__(*args, **kwargs)

    class DaemonRunnerStopFailureError(DaemonRunnerError, RuntimeError):
        """ Raised when failure stopping DaemonRunner. """

    def _remove(self):
        print('removed pidfile %s' % self.pidfile)
        os.remove(self.pidfile)

    def is_running(self, pid) -> bool:
        try:
            p = psutil.Process(pid)
            p.terminate()
        except OSError:
            print("can't deliver signal to %s" % pid)
            return False
        return True

    def run_driver(self):
        p, output, error = popen_communicate(self.cmd, env.DRIVER_LOG)
        if p.returncode != 0 or "error" in error:
            raise Exception(error)

    def start(self):
        if not self.pidfile.is_locked():
            print("==> starting")
            time.sleep(.25)
            with self.context:
                self.run_driver()
        else:
            print(f"lockfile.AlreadyLocked: {self.pidfile} (pid={self.pidfile.read_pid()}) is already locked")

    def get_pid(self, lockfile) -> int:
        with open(lockfile, 'r') as f:
            if os.stat(lockfile).st_size == 0:
                print(f"{lockfile} is empty")
                quit()
            try:
                pidstr = f.read().strip()
                return int(pidstr)
            except ValueError:
                # not an integer
                print("not an integer: %s" % pidstr)
                raise

    def terminate(self):
        f = env.DRIVER_LOCKFILE  # kill the Driver started using popen_communicate()
        if os.path.isfile(f):
            try:
                pid = self.get_pid(f)
                try:
                    while self.is_running(pid):
                        time.sleep(.25)
                except OSError as err:
                    if err.errno == errno.ESRCH:
                        raise(str(err))
                finally:
                    open(f, 'w').close()

            except psutil.NoSuchProcess:
                open(f, 'w').close()
            except Exception as e:
                raise e

            print(f"==> terminated //{f} is_locked={self.pidfile.is_locked()}")
        else:
            print("There is no daemon to terminate")

    def restart(self):
        try:
            self.terminate()
            time.sleep(.25)
        except:
            print("daemon is not running on the background")

        self.start()
        print("==> restarted")
