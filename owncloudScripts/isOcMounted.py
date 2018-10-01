#!/usr/bin/env python

import os, owncloud, subprocess, sys
# sys.path.insert(1, os.path.join(sys.path[0], '..'))
# import lib

def isOcMounted(): #{
    dir_name='/home/alper/ocClient'
    try:
        # cmd: findmnt --noheadings -lo source $HOME/oc
        res = subprocess.check_output(['findmnt', '--noheadings', '-lo', 'source', dir_name]).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        res = ''
        
    if not 'b2drop.eudat.eu/remote.php/webdav/' in res:
        print('Mount a folder in order to access EUDAT(https://b2drop.eudat.eu/remote.php/webdav/). Please do: \n' \
              'mkdir -p $HOME/oc \n' \
              'sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ $HOME/oc')    
    return True
#}

if __name__ == "__main__":
    print(isOcMounted())
