#!/usr/bin/env python3

import subprocess, sys, os
import lib
from contractCalls.submitJob import submitJob

if len(sys.argv) < 2:
    print('Please provide folder type: tar/folder')
    sys.exit()

folderType = sys.argv[1]
folderToShare  = 'exampleFolderToShare'
clusterToShare = 'alper.alimoglu@gmail.com' # 'alper01234alper@gmail.com'

# subprocess.run(['sudo', 'chmod', '-R', '777', folderToShare])

if folderType == 'folder': 
    tarHash = subprocess.check_output(['../scripts/generateMD5sum.sh', folderToShare]).decode('utf-8').strip()                        
    tarHash = tarHash.split(' ', 1)[0]
    print('hash=' + tarHash)

    if not os.path.isdir(tarHash):
        subprocess.run(['cp', '-a', folderToShare, tarHash])
    folderToShare = tarHash

    #cmd: gdrive list --query "name contains 'exampleFolderToShare'" --no-header
    res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + folderToShare + '\'', '--no-header']).decode('utf-8').strip()
    if res is '':
        print('Uploading ...')
        #cmd: gdrive upload --recursive $folderToShare
        res = subprocess.check_output(['gdrive', 'upload', '--recursive', folderToShare]).decode('utf-8').strip()
        print(res)    
        res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + folderToShare + '\'', '--no-header']).decode('utf-8').strip()
elif folderType == 'tar':
    if len(sys.argv) == 3:
        tarHash = sys.argv[2]        
    else:
        subprocess.run(['chmod', '-R', '777', folderToShare])
        # Tar produces different files each time: https://unix.stackexchange.com/a/438330/198423
        # find exampleFolderToShare -print0 | LC_ALL=C sort -z | GZIP=-n tar --no-recursion --null -T - -zcvf exampleFolderToShare.tar.gz
        p1 = subprocess.Popen(['find', folderToShare, '-print0'], stdout=subprocess.PIPE)
        #-----------
        p2 = subprocess.Popen(['sort', '-z'], stdin=p1.stdout, stdout=subprocess.PIPE, env={'LC_ALL': 'C'})
        p1.stdout.close()
        #-----------
        p3 = subprocess.Popen(['tar', '--no-recursion', '--null', '-T', '-', '-zcvf', folderToShare + '.tar.gz'], stdin=p2.stdout,stdout=subprocess.PIPE, env={'GZIP': '-n'})
        p2.stdout.close()
        #-----------
        p3.communicate()        
        # subprocess.run(['sudo', 'tar', 'zcf', folderToShare + '.tar.gz', folderToShare])
        tarHash = subprocess.check_output(['md5sum', folderToShare + '.tar.gz']).decode('utf-8').strip()
        tarHash = tarHash.split(' ', 1)[0]
        print('hash=' + tarHash)
        subprocess.run(['mv', folderToShare + '.tar.gz', tarHash + '.tar.gz'])                
        subprocess.run(['gdrive', 'upload', tarHash + '.tar.gz'])    
        subprocess.run(['rm', '-f', tarHash + '.tar.gz'])
        
    res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + tarHash + '.tar.gz' + '\'', '--no-header']).decode('utf-8').strip()
elif folderType == 'zip':
    if len(sys.argv) == 3:
        tarHash = sys.argv[2]        
    else:
        # zip -r myfiles.zip mydir
        subprocess.run(['zip', '-r', folderToShare + '.zip', folderToShare])
        tarHash = subprocess.check_output(['md5sum', folderToShare + '.zip']).decode('utf-8').strip()
        tarHash = tarHash.split(' ', 1)[0]            
        subprocess.run(['mv', folderToShare + '.zip', tarHash + '.zip'])    
        subprocess.run(['gdrive', 'upload', tarHash + '.zip'])    
        subprocess.run(['rm', '-f', tarHash + '.zip'])
    print('hash=' + tarHash)
    res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + tarHash + '.zip' + '\'', '--no-header']).decode('utf-8').strip()

jobKey = res.split(' ')[0]
print('jobKey=' + jobKey)
#cmd: gdrive share $jobKey --role writer --type user --email $clusterToShare
res = subprocess.check_output(['gdrive', 'share', jobKey, '--role', 'writer', '--type', 'user', '--email', clusterToShare]).decode('utf-8').strip()
print('share_output=' + res)

print('\nSubmitting Job...')
clusterID='0x4e4a0750350796164D8DefC442a712B7557BF282'
coreNum=1
coreMinuteGas=5

gasBandwidthInMB  = 100
gasBandwidthOutMB = 100
gasBandwidthMB    = gasBandwidthInMB + gasBandwidthOutMB

jobDescription='science'
storageID=4
cacheType = lib.cacheType.private
# cacheType = lib.cacheType.public
accountID=0

res = submitJob(str(clusterID), str(jobKey), coreNum, coreMinuteGas, gasBandwidthMB, str(jobDescription), storageID, str(tarHash), cacheType, accountID)
print(res)
