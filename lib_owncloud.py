#!/usr/bin/env python3

import subprocess, sys, lib, os, traceback

def singleFolderShare(folderName, oc, fID):
    try:
        # folderNames = os.listdir('/oc')
        # fID = '5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu'
        if not oc.is_shared(folderName):
            oc.share_file_with_user(folderName, fID, remote_user=True, perms=31)
            return 'Sharing is completed successfully.'
        else:
            return 'Requester folder is already shared.'
    except Exception:
        print(traceback.format_exc())
        sys.exit()

def eudatInitializeFolder(folderToShare, oc):    
    dir_path = os.path.dirname(folderToShare)    
    tarHash  = lib.compressFolder(folderToShare)
    try:
        res = oc.mkdir(tarHash)
    except Exception:
        print('Folder is already created.')
        # print(traceback.format_exc())

    print('./' + tarHash + '/' + tarHash + '.tar.gz', tarHash + '.tar.gz')
    try:
        status = oc.put_file('./' + tarHash + '/' + tarHash + '.tar.gz', dir_path + '/' + tarHash + '.tar.gz')
        if not status:
            sys.exit()

        # oc_path='/oc'
        # print(oc_path + '/' + tarHash)
        # res = subprocess.check_output(['sudo', 'rsync', '-avhW', '--progress', tarHash + '.tar.gz', oc_path + '/' + tarHash + '/']).decode('utf-8').strip()
        subprocess.run(['rm', '-f', dir_path + '/' + tarHash + '.tar.gz'])
    except Exception:
        print(traceback.format_exc())
        sys.exit()

    return tarHash

def isOcMounted() -> bool:
    dir_name = '/oc'
    res = None
    try:
        # cmd: findmnt --noheadings -lo source $HOME/oc
        res = subprocess.check_output(['findmnt', '--noheadings', '-lo', 'source', dir_name]).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(str(e))
        return False
        
    if not 'b2drop.eudat.eu/remote.php/webdav/' in res:
        print('Mount a folder in order to access EUDAT(https://b2drop.eudat.eu/remote.php/webdav/).\n' \
              'Please do: \n' \
              'mkdir -p /oc \n' \
              'sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ /oc')
        return False
    else:
        return True
