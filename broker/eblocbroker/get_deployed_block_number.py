#!/usr/bin/env python3

import broker.cfg as cfg

if __name__ == "__main__":
    print(cfg.Ebb.get_deployed_block_number())
