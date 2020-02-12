#!/usr/bin/env python3

import os
import subprocess
import sys

import owncloud

from lib_owncloud import isOcMounted

if __name__ == "__main__":
    print(isOcMounted())
