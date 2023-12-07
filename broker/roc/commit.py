#!/usr/bin/env python3

from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.errors import QuietExit
from broker import cfg, config
from broker.config import env


Ebb = cfg.Ebb
Ebb.get_block_number()


def commit_hash(_hash):
    roc_num = config.roc.getTokenIndex(_hash)
    if roc_num == 0:
        fn = env.PROVIDER_ID.lower().replace("0x", "") + ".json"
        Ebb.brownie_load_account(fn)
        config.roc.createCertificate(env.PROVIDER_ID, _hash, {"from": env.PROVIDER_ID})
    else:
        log(f"Nothing to do... {_hash} => {roc_num}")


def main():
    log(config.roc.name())
    _hash = "50c4860efe8f597e39a2305b05b0c299"
    commit_hash(_hash)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
