#!/usr/bin/env python3

def isWeb3Connected(web3=None): 
    if web3 is None:
        import os, sys
        from os.path import expanduser
        home = expanduser("~")

        from web3 import Web3
        from web3.providers.rpc import HTTPProvider
        from web3 import Web3, IPCProvider
        sys.path.insert(1, os.path.join(sys.path[0], '..'))
        import lib
        if lib.POA_CHAIN == 0:
            # Note that you should create only one RPCProvider per process,
            # as it recycles underlying TCP/IP network connections between
            # your process and Ethereum node
            web3 = Web3(HTTPProvider('http://localhost:' + str(lib.RPC_PORT)))
        else: 
            web3 = Web3(IPCProvider(home + '/eBlocPOA/private/geth.ipc')) 
            from web3.middleware import geth_poa_middleware
            # inject the poa compatibility middleware to the innermost layer
            web3.middleware_stack.inject(geth_poa_middleware, layer=0)

    return web3.isConnected()

if __name__ == '__main__': 
    print(isWeb3Connected())
