#!/usr/bin/env python3

from broker import cfg
from broker.config import env
from broker.utils import print_tb


def main():
    Ebb = cfg.Ebb
    try:
        Ebb.allowance(env.CONTRACT_ADDRESS, 0x378181CE7B07E8DD749C6F42772574441B20E35F)
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    main()
