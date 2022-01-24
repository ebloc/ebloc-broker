#!/usr/bin/env python3

from broker import cfg


def main():
    print(cfg.Ebb.get_deployed_block_number())


if __name__ == "__main__":
    main()
