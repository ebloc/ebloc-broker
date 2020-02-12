#!/usr/bin/env python3

import logging

import Colorer


def load_log():
    from lib import LOG_PATH

    logging.basicConfig(
        level=logging.INFO,
        # format="%(asctime)s %(levelname)-8s [%(module)s %(lineno)d] %(message)s",
        # format="%(asctime)s %(levelname)-8s [%(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
        format="[%(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
        handlers=[logging.FileHandler(f"{LOG_PATH}/transactions/providerOut.txt"), logging.StreamHandler()],
    )
    return logging
