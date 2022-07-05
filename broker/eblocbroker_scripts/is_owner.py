#!/usr/bin/env python3

# Example usage: ./is_owner.py 0x57b60037b82154ec7149142c606ba024fbb0f991

import sys

from broker import cfg


def main():
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        addr = str(sys.argv[1])
        print(Ebb.is_owner(addr))
    else:
        print("E: Please provide an Ethereum address as an argument.")


if __name__ == "__main__":
    main()
