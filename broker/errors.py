class BashCommandsException(Exception):
    def __init__(self, returncode, output, error_msg, cmd):
        self.returncode = returncode
        self.output = output
        self.error_msg = error_msg
        self.cmd = cmd
        Exception.__init__("Error in the executed command")


class JobException(Exception):
    """Generate job info exception to prevent to print the trace."""


class IpfsNotConnected(Exception):
    """Attempt to connect to IPFS is failed."""


class HandlerException(Exception):
    """Generate HandlerException."""


class Terminate(Exception):
    """Terminate the process."""


class Timeout(Exception):
    """Timeout."""


class Web3NotConnected(Exception):
    """Web3 is not connected."""


class QuietExit(Exception):
    """Exit quietly without printing the trace."""


class QuietTerminate(Exception):
    """Terminate the process."""
