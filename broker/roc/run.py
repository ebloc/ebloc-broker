#!/usr/bin/env python3

from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.errors import QuietExit
from broker.lib import run
from broker import cfg, config
from broker.config import env
import sys
import fileinput

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


def main():
    bn = Ebb.get_block_number()
    print(f"block_number={bn}")
    _hash = "abcd"
    for line in fileinput.input([env.EBLOCPATH / "broker" / "roc" / "request.sh"], inplace=True):
        if line.strip().startswith("crid="):
            line = f'crid="{_hash}"\n'

        if line.strip().startswith("public_key="):
            line = f'public_key="{env.PROVIDER_ID}"\n'

        sys.stdout.write(line)

    #: takes long time ~30 seconds
    run(["bash", env.EBLOCPATH / "broker" / "roc" / "request.sh"])
    roc_id = roc(from_block=bn, provider=env.PROVIDER_ID)
    print(f"roc={roc_id}")
    # TODO: deploy Auto => Bloxberg


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
