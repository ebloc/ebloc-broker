#!/usr/bin/env python3

import fileinput
import sys

from broker import cfg, config
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.config import env
from broker.errors import QuietExit
from broker.lib import run

Ebb = cfg.Ebb


def roc(from_block=23066710, provider="0x29e613B04125c16db3f3613563bFdd0BA24Cb629") -> int:
    roc_id: int = 0
    event_filter = config._roc.events.Transfer.createFilter(
        argument_filters={"to": str(provider)},
        fromBlock=from_block,
        toBlock="latest",
    )
    for logged_receipt in event_filter.get_all_entries():
        #: should be single event is triggered
        log(logged_receipt.args)
        roc_id = logged_receipt.args["tokenId"]

    return roc_id


def commit_hash(_hash, bn):
    roc()
    roc(provider=env.PROVIDER_ID)
    """
    output = config.auto.getFromHashToRoc(_hash)
    if output > 0:
        log(f"Already committed hash, roc={output}")
        return
    """

    for line in fileinput.input([env.EBLOCPATH / "broker" / "roc" / "request.sh"], inplace=True):
        if line.strip().startswith("crid="):
            line = f'crid="{_hash}"\n'

        if line.strip().startswith("public_key="):
            line = f'public_key="{env.PROVIDER_ID}"\n'

        sys.stdout.write(line)

    #: takes long time ~30 seconds
    run(["bash", env.EBLOCPATH / "broker" / "roc" / "request.sh"])
    roc_id = roc(from_block=bn - 1, provider=env.PROVIDER_ID)
    print(f"roc={roc_id}")
    if int(roc_id) > 0:
        # TODO: deploy Auto => Bloxberg
        fn = env.PROVIDER_ID.lower().replace("0x", "") + ".json"
        Ebb.brownie_load_account(fn)
        config.auto.hashToRoc(_hash, roc_id, False, {"from": env.PROVIDER_ID})
    else:
        log("E: something went wrong")


def main():
    bn = Ebb.get_block_number()
    # print(config.auto.getAutonomousSoftwareOrgInfo())
    print(f"block_number={bn}")
    _hash = "50c4860efe8f597e39a2305b05b0c299"
    commit_hash(_hash, bn)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
