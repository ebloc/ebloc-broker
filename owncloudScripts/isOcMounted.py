#!/usr/bin/env python

import os, owncloud, subprocess
from os.path import expanduser
home = expanduser("~")
dir_name=  home + '/oc'

try:
    # cmd: findmnt --noheadings -lo source $HOME/oc
    res = subprocess.check_output(['findmnt', '--noheadings', '-lo', 'source', dir_name]).decode('utf-8').strip()
except subprocess.CalledProcessError as e:
    res = ''
    
if not 'b2drop.eudat.eu/remote.php/webdav/' in res:
    print('Mount a folder in order to access EUDAT(https://b2drop.eudat.eu/remote.php/webdav/). Please do: \n' \
          'mkdir -p $HOME/oc \n' \
          'sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ $HOME/oc')
    
print('True')
