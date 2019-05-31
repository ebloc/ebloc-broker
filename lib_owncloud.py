#!/usr/bin/env python3

import subprocess, sys, lib

def singleFolderShare(folderName, oc, fID):
    # folderNames = os.listdir(home + "/oc")
    # fID = '5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu'
    if not oc.is_shared(folderName):
        oc.share_file_with_user(folderName, fID, remote_user=True, perms=31)
        return 'Sharing is completed successfully.'
    else:
        return 'Already shared.'

def eudatInitializeFolder(folderToShare, oc):
    if "/" in folderToShare:
        print('Please provide folder onyour current directory.')
        sys.exit()

    tarHash = lib.compressFolder(folderToShare)
    try:
        res = oc.mkdir(tarHash)
    except:
        print('Already created directory under oc')

    print('./' + tarHash + '/' + tarHash + '.tar.gz', tarHash + '.tar.gz')
    res = oc.put_file('./' + tarHash + '/' + tarHash + '.tar.gz', tarHash + '.tar.gz')
    if not res:
        sys.exit()

    # ocClient='/home/alper/ocClient'
    # res = subprocess.check_output(['sudo', 'rsync', '-avhW', '--progress', tarHash + '.tar.gz', ocClient + '/' + tarHash + '/']).decode('utf-8').strip()
    # print(ocClient + '/' + tarHash)
    subprocess.run(['rm', '-f', tarHash + '.tar.gz'])
    return tarHash

def isOcMounted():
    dir_name = '/oc'
    try:
        # cmd: findmnt --noheadings -lo source $HOME/oc
        res = subprocess.check_output(['findmnt', '--noheadings', '-lo', 'source', dir_name]).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        res = ''

    if not 'b2drop.eudat.eu/remote.php/webdav/' in res:
        print('Mount a folder in order to access EUDAT(https://b2drop.eudat.eu/remote.php/webdav/).\n' \
              'Please do: \n' \
              'mkdir -p /oc \n' \
              'sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ /oc')
        return False
    else:
        return True
