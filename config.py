#!/usr/bin/env python3

import logging

import Colorer

eBlocBroker = None
w3 = None
driver_cancel_process = None
whisper_state_receiver_process = None


def load_log(log_path=""):
    log = logging.getLogger()  # root logger
    for hdlr in log.handlers[:]:  # remove all old handlers
        log.removeHandler(hdlr)

    if log_path == "":
        from lib import LOG_PATH

        log_path = f"{LOG_PATH}/transactions/providerOut.txt"

    logging.basicConfig(
        level=logging.INFO,
        # format="%(asctime)s %(levelname)-8s [%(module)s %(lineno)d] %(message)s",
        # format="%(asctime)s %(levelname)-8s [%(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
        format="[%(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
    )
    return logging
