#!/usr/bin/env python3

import os, owncloud, subprocess, sys
from lib_owncloud import isOcMounted

if __name__ == "__main__":
    print(isOcMounted())
