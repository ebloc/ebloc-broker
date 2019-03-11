#!/usr/bin/env python3

import os, owncloud, subprocess, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from lib_owncloud import isOcMounted

if __name__ == "__main__":
    print(isOcMounted())   
