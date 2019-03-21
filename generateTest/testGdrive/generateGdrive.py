#!/usr/bin/env python3

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys, subprocess
from os.path import expanduser
from random import randint
home = expanduser("~")
sys.path.insert(0, home + '/eBlocBroker')
from lib_owncloud import singleFolderShare, eudatInitializeFolder
path = os.getcwd()
os.environ['path'] = path

clusterToShare = "alper.alimoglu@gmail.com"
flag        = 0
counter     = 0
itemsToScan = 2#151
hashesFile = open(path + '/hashOutput.txt', 'w+')
with open(path + "/../nasa.txt") as test:
    for line in test:
        f = open("../ipfs/run.sh", 'w+')
        lineIn = line.split(" ")
        if int(lineIn[1]) - int(lineIn[0]) > 60 and int(lineIn[2]) != 0:
            print("Time to take in seconds: "  + str(int(lineIn[1]) - int(lineIn[0])))
            print("CoreNum: "  + str(int(lineIn[2])))
            print(line)
            with open("../ipfs/run_temp.sh") as ff:
                for line in ff:
                    f.write(line)

            randomHash = str(random.getrandbits(128)) + str(random.getrandbits(128))
            f.write("sleep " + str(int(lineIn[1]) - int(lineIn[0])) + "\n")
            f.write("#" + randomHash + "\n") # Add random line to create different hash
            f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > completed.txt\n")
            f.close()

            folderToShare = "../ipfs"
            tarHash = subprocess.check_output(['../../scripts/generateMD5sum.sh', folderToShare]).decode('utf-8').strip()
            tarHash = tarHash.split(' ', 1)[0]
            print('SourecodeHash=' + tarHash)
            
            os.environ['fileName']       = tarHash
            os.environ['clusterToShare'] = 'alper01234alper@gmail.com';

            subprocess.run(['cp', '-a', '../ipfs', '../' + tarHash])
            
            print('Uploading ...')
            # rclone copy ipfs remote:ipfs
            res = subprocess.check_output(['rclone', 'copy', '../ipfs', 'remote:' + tarHash]).decode('utf-8').strip()
            print(res)

            while True:
                try:
                    res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + tarHash + '\'', '--no-header']).decode('utf-8').strip()
                    # print(res)
                    jobKey = res.split(' ')[0]
                    print(jobKey)
                except Exception as e:
                    time.sleep(1)
                    print(e.output.decode('utf-8').strip())
                else:
                    break

            while True:    
                try:
                    # jobKey = "1H9XSDzj15m_2IdNcblAzxk5VRWxF0CIP"
                    res = subprocess.check_output(['gdrive', 'share', jobKey, '--role', 'writer', '--type', 'user', '--email',
                                           clusterToShare]).decode('utf-8').strip()
                    print(res)
                except Exception as e:
                    time.sleep(1)
                    print(e.output.decode('utf-8').strip())
                else:
                    break

                            
            # print(os.popen('gdrive upload --recursive $fileName && jobKey=$(gdrive list | grep $fileName | awk \'{print $1}\') && echo $jobKey; gdrive share $jobKey  --role writer --type user --email $clusterToShare;').read())
            sys.exit()

            time.sleep(1)
            # After run.sh is update share the ipfs through eudat
            print(singleFolderShare(tarHash, oc))
            if flag == 1:
                hashesFile.write(" " + str(int(lineIn[0])-startTimeTemp) + '\n')

            flag = 1
            startTimeTemp = int(lineIn[0])
            print("Shared Job#" + str(counter))
            counter += 1
            if counter == itemsToScan:
                break

            hashesFile.write(tarHash + " " + str(int(lineIn[1]) - int(lineIn[0])) + " " + str(int(lineIn[2])) + " " + str(int(lineIn[0])) + " " +
                             str(int(lineIn[1])) + " " + tarHash)

hashesFile.close()
print('\nFolders are created. Sharing files now...')


'''
#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint
sys.path.insert(0, '/home/prc/eBlocBroker/test')
from func import testFunc

path =os.getcwd(); os.environ['path'] = path;

def contractCall( val ):
   return os.popen( val + "| node").read().replace("\n", "").replace(" ", "");

def log(strIn):
   print(strIn)
   txFile  = open(path + '/clientOutput.txt', 'a'); 
   txFile.write(strIn + "\n"); 
   txFile.close();

header     = "var mylib = require('" + "/home/prc/eBlocBroker/eBlocBrokerHeader.js')"; os.environ['header'] = header;

# Definitions ===========================================
testType     = 'gdrive';
workloadTest = 'nasa.txt';
readTest     = 'hashOutput.txt';
clusterID = "0xf20b4c9068a3945ce5cd73d50fdabbf04412e421";
os.environ['clusterID'] = clusterID;
# =======================================================

input('> Are you sure want to overwrite ' + readTest + '?');
counter = 0;
itemsToScan = 300;
hashesFile = open(path + '/' + readTest, 'w+')
commentStr = "QmQANSjxQaziHPdMuj37LC53j65cVtXXwQYvu8GxJCPFJE"; #dummy hash string.
with open(path + "/nasa.txt") as test:
    for line in test:
        f = open(path + '../ipfs/run.sh', 'w+')
        lineIn = line.split(" ");

        if ((int(lineIn[1]) - int(lineIn[0])) > 60 ):
           print( "Time to take in seconds: "  + str(int(lineIn[1]) - int(lineIn[0])) )
           print( "CoreNum: "  + str(int(lineIn[2])) )
           print(line)

           with open(path + "../ipfs/run_temp.sh") as ff:
              for line in ff:
                 f.write(line);

           commentStr = str(random.getrandbits(128)) #Generates Random Hash.
           os.environ['commentStr'] = commentStr;
           print(commentStr)

           f.write("sleep " + str(int(lineIn[1]) - int(lineIn[0])) + "\n");
           f.write("#" + commentStr + "\n"); #add random line to create different hash.
           f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > " + commentStr + ".txt\n"); #add random line to create different hash.
           f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > completed.txt\n" ); #add random line to create different hash.
           f.close();

           os.system('cp -a ipfs/ $commentStr/');
           
           os.environ['fileName']       = commentStr;
           os.environ['clusterToShare'] = 'alper01234alper@gmail.com';

           print(os.popen('gdrive upload --recursive $fileName && jobKey=$(gdrive list | grep $fileName | awk \'{print $1}\') && echo $jobKey; gdrive share $jobKey  --role writer --type user --email $clusterToShare;').read());

           jobKey = os.popen('jobKey=$(gdrive list | grep $fileName | awk \'{print $1}\') && echo $jobKey').read().rstrip('\n');
           
           print('jobKey: ' + jobKey)

           if jobKey != '':
              hashesFile.write(jobKey + " " + str(int(lineIn[1]) - int(lineIn[0])) + " " + str(int(lineIn[2])) + "\n");
              
           if (counter == itemsToScan):
              break;

           os.system('rm -rf $commentStr');
           
           print(counter)
           counter += 1;
hashesFile.close();
sys.exit()
'''
