class BashCommandsException(Exception):
    def __init__(self, returncode, output, error_msg):
        self.returncode = returncode
        self.output = output
        self.error_msg = error_msg
        Exception.__init__("Error in the executed command")


class HandlerException(Exception):
    """Generate HandlerException."""


class JobException(Exception):
    """Trace is not printed."""


class Web3NotConnected(Exception):
    """Web3 is not connected."""


class QuietExit(Exception):
    """Trace is not printed."""
