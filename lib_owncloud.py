#!/usr/bin/env python3

import subprocess, sys

def singleFolderShare(folderName, oc):
    # folderNames = os.listdir(home + "/oc")    
    if not oc.is_shared(folderName):
        oc.share_file_with_user(folderName, '5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu', remote_user=True, perms=31)
        return 'Sharing is completed successfully.'
    else:
        return 'Already shared.'

def eudatInitializeFolder(folderToShare, oc):
    if "/" in folderToShare:
        print('Please provide folder onyour current directory.')
        sys.exit()

    subprocess.run(['chmod', '-R', '777', folderToShare])
    # Tar produces different files each time: https://unix.stackexchange.com/a/438330/198423
    # find exampleFolderToShare -print0 | LC_ALL=C sort -z | GZIP=-n tar --absolute-names --no-recursion --null -T - -zcvf exampleFolderToShare.tar.gz
    p1 = subprocess.Popen(['find', folderToShare, '-print0'], stdout=subprocess.PIPE)
    #-----------
    p2 = subprocess.Popen(['sort', '-z'], stdin=p1.stdout, stdout=subprocess.PIPE, env={'LC_ALL': 'C'})
    p1.stdout.close()
    #-----------
    p3 = subprocess.Popen(['tar', '--absolute-names', '--no-recursion', '--null', '-T', '-', '-zcvf', folderToShare + '.tar.gz'],
                          stdin=p2.stdout,stdout=subprocess.PIPE, env={'GZIP': '-n'})
    p2.stdout.close()
    #-----------
    p3.communicate()
    # subprocess.run(['sudo', 'tar', 'zcf', folderToShare + '.tar.gz', folderToShare])
    tarHash = subprocess.check_output(['md5sum', folderToShare + '.tar.gz']).decode('utf-8').strip()
    tarHash = tarHash.split(' ', 1)[0]    
    print('hash=' + tarHash)
    subprocess.run(['mv', folderToShare + '.tar.gz', tarHash + '.tar.gz'])
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
