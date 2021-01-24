import os

import config
import eblocbroker.Contract as Contract

WHOAMI = os.getenv("WHOAMI")
config.Ebb = Contract.eblocbroker
