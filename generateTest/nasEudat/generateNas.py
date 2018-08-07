#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint
sys.path.insert(0, '/home/prc/eBlocBroker/test')
from func import testFunc

path = os.getcwd();
os.environ['path'] = path;

def contractCall( val ):
   return os.popen( val + "| node").read().replace("\n", "").replace(" ", "");

def log(strIn): #{
   print( strIn )
   txFile     = open( '/home/prc/multiple/nasEudat' + '/clientOutput.txt', 'a'); 
   txFile.write( strIn + "\n" ); 
   txFile.close();
#}

# Login to EUDAT account----------------------------------------
f = open( path+"/password.txt", 'r'); # Password read from the file. 
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('alper.alimoglu@boun.edu.tr', password )
#---------------------------------------------------------------
SHARE_PATH = path + "/oc"
header     = "var mylib = require('" + "/home/prc/eBlocBroker/eBlocBrokerHeader.js')";
os.environ['header'] = header;

# Definitions ===========================================
testType     = 'eudat-nas';
workloadTest = 'nasa.txt';
readTest     = 'hashOutput.txt';
# =======================================================
itemsToScan = 100;
counter     = 0;
hashesFile  = open(path + '/' + readTest, 'w+')
startTime   = 1;
coreLimit   = 7200; #120*60 (2 hours money is paid)

while(True): #{
        if(counter >= itemsToScan):
           break
        f = open(path + '/ipfs/run.sh', 'w+')
        with open(path + "/ipfs/run_temp.sh") as ff:
            for line in ff:
                f.write(line);
        commentStr = str(random.getrandbits(128)) # Generates random hash.
        print( commentStr )

        testId  = randint(0, 3);
        coreNum = 1; # randint(1, 2);
        
        if(testId == 0):
           f.write("make bt CLASS=B\n")
           f.write("mpirun -n " + str(coreNum) + " bin/bt.B.x inputbt.data")
        elif(testId == 1):
           f.write("make sp CLASS=B\n")
           f.write("mpirun -n " + str(coreNum) + " bin/sp.B.x inputsp.data")
        elif(testId == 2):
           f.write("make ua CLASS=B\n")
           f.write("mpirun -n " + str(coreNum) + " bin/ua.B.x inputua.data")
        elif(testId == 3):
           f.write("make lu CLASS=B\n")
           f.write("mpirun -n " + str(coreNum) + " bin/lu.B.x inputlu.data")
        f.close();

        copyIntoSharePath=SHARE_PATH + "/" + commentStr;
        os.environ['copyIntoSharePath'] = copyIntoSharePath;

        if not os.path.isdir(copyIntoSharePath):
            os.makedirs( copyIntoSharePath )

        os.chdir(path + "/ipfs")    
        os.popen('tar -P -cvzf /home/prc/multiple/nasEudat/ipfs.tar.gz  .' ).read();
        os.popen("cp -a /home/prc/multiple/nasEudat/ipfs.tar.gz $copyIntoSharePath")

        hashesFile.write( commentStr + " " + str(startTime) + " " + str(coreNum) + " " + str(startTime + coreLimit) + "\n" ); ##
        startTime = startTime + randint(300, 600); # Sleep between 5 to 10 minutes.
        counter += 1;
        time.sleep(1);
#}
hashesFile.close();

with open(path + '/' + readTest) as f: #{
   fileR = open(path + "/" + workloadTest, 'w'); # Put fixed file name.
   for line in f:      
      l = line.split(" ")
      fileR.write(str(int(l[1])) + " " + str(7200 + int(l[1])) + " " + str(int(l[2]))  + " 7200\n")
   fileR.close();
#}

print('Sharing files now...')
print(os.popen('python $path/shareOwnCloud.py').read());
