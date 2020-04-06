#!/usr/bin/env python3
import os
import sys

import config


def WHERE(back=0):
    try:
        frame = sys._getframe(back + 1)
    except:
        frame = sys._getframe(1)
    return "%s:%s %s()" % (os.path.basename(frame.f_code.co_filename), frame.f_lineno, frame.f_code.co_name)


def init_env():
    if not config.env:
        config.env = config.ENV()
    return config.env
