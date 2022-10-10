class BashCommandsException(Exception):
    def __init__(self, returncode, output, error_msg, cmd):
        self.cmd = cmd
        self.returncode = returncode
        self.output = output
        self.error_msg = error_msg
        Exception.__init__("Error in the executed command")


class JobException(Exception):
    """Generate job info exception to prevent trace to be printed."""


class HandlerException(Exception):
    """Generate HandlerException."""


class IpfsNotConnected(Exception):
    """Attempt to connect to IPFS is failed."""


class Terminate(Exception):
    """Terminate the process."""


class Timeout(Exception):
    """Timeout."""


class Web3NotConnected(Exception):
    """Web3 is not connected."""


class QuietExit(Exception):
    """Exit quietly without printing the trace."""
