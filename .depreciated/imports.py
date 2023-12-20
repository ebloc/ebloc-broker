#!/usr/bin/env python3

from web3 import IPCProvider, Web3
from web3.middleware import geth_poa_middleware
from web3.providers.rpc import HTTPProvider

from broker.utils import is_geth_on, run, terminate


def _connect_to_web3() -> None:
    """Connect to web3 of the corresponding ethereum blockchain.

    * bloxberg:
    __ https://bloxberg.org
    """
    if env.IS_GETH_TUNNEL or not env.IS_EBLOCPOA:
        if env.IS_TESTNET:
            # TODO you can use brownie's connected web3?
            cfg.w3 = Web3(HTTPProvider("https://core.bloxberg.org"))
        else:
            cfg.w3 = Web3(HTTPProvider(f"http://localhost:{env.RPC_PORT}"))
    else:
        cfg.w3 = Web3(IPCProvider(env.DATADIR.joinpath("geth.ipc")))
        #: inject the poa compatibility middleware to the innermost layer
        cfg.w3.middleware_onion.inject(geth_poa_middleware, layer=0)


def connect_to_web3() -> None:
    """Connect to the private ethereum network using web3.

    Note that you should create only one RPC Provider per process, as it
    recycles underlying TCP/IP network connections between your process and
    Ethereum node
    """
    if cfg.w3.isConnected():
        return

    web3_ipc_fn = env.DATADIR.joinpath("geth.ipc")
    for _ in range(5):
        _connect_to_web3()
        if not cfg.w3.isConnected():
            try:
                if env.IS_GETH_TUNNEL:
                    raise Exception("Web3ConnectError: try tunnelling: ssh -f -N -L 8545:localhost:8545 username@<ip>")

                if env.IS_TESTNET:
                    log("E: web3 is not connected into [green]BLOXBERG[/green]")
                else:
                    is_geth_on()
            except QuietExit:
                pass
            except Exception as e:
                print_tb(e)
                sys.exit(1)

            if not env.IS_GETH_TUNNEL and not env.IS_TESTNET:
                log(
                    "E: If web3 is not connected please start geth server and give permission \n"
                    "to /private/geth.ipc file doing: ",
                    end="",
                )
                log(f"sudo chown $(logname) {web3_ipc_fn}", "green")
                log(f"==> running `sudo chown $(whoami) {web3_ipc_fn}`")
                run(["sudo", "chown", env.WHOAMI, web3_ipc_fn])
        else:
            break
    else:
        terminate(is_traceback=False)
