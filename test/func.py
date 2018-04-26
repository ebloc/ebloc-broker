import os, time, math, random, sys
from random import randint

def log(strIn, path):
   print( strIn )
   txFile     = open(path + '/clientOutput.txt', 'a'); 
   txFile.write( strIn + "\n" ); 
   txFile.close();

def testFunc(path, readTest, workloadTest, testType, clusterID): #{
  os.environ['clusterID']     = clusterID;

  ipfsHashNo = {} #create a dictionary called ipfsHashNo
  lineNumCounter = 0;
  with open(path + '/' + readTest) as test:
      for line in test:
          ipfsHashNo[lineNumCounter] = line.rstrip(); # Assign value to key counter.
          lineNumCounter += 1

  f       = open(path + "/" + workloadTest); #put fixed file name.
  line1   = f.readline();
  line1_in = line1.split(" ")

  counter      = 0;
  printCounter = counter;
  skippedLines = 0;


  while True: #{
    if counter >= 0:
        if counter >= len(ipfsHashNo):
           log("Exceed hashOutput.txt's limit Total item number: " + str(len(ipfsHashNo)), path)
           break;

        line2          = f.readline();
        line2_splitted = line2.split(" ")
        ipfsHash = ipfsHashNo[counter].split(" ");

        if str(ipfsHash[1]) != '0' and (line2_splitted[0] != line2_splitted[1]) and (int(ipfsHash[2]) != 0): # Requested core shouldn't be 0.
           if not line2:
              break  # EOF
           line2_in = line2.split(" ")
           sleepTime = str(int(line2_in[0]) -  int(line1_in[0])); # time to sleep in seconds

           blockNumber = os.popen('python /home/prc/eBlocBroker/contractCalls/blockNumber.py').read().rstrip('\n');
           log("\n------------------------------------------", path)
           log("Job: " + str(counter-skippedLines) + "| Current Time: " + time.ctime() +"| BlockNumber: " + blockNumber, path);
           log("Nasa Submit range: " + line2_splitted[0] + " " + line2_splitted[1], path)
           log("Sleep Time to submit next job: " + sleepTime, path)
           log(ipfsHashNo[counter], path)

           eudatFlag = 0;
           if (testType == 'eudat'):
              os.environ['ipfsHash'] = str(ipfsHash[0]);
              os.environ['type']     = '1';
           elif (testType == 'eudat-nas'):
              os.environ['ipfsHash'] = str(ipfsHash[0]);
              os.environ['type']     = '1';
              eudatFlag = 1;
           elif (testType == 'ipfs'):
              os.environ['ipfsHash'] = str(ipfsHash[0]);
              os.environ['type']     = '0';
           elif (testType == 'ipfsMiniLock'):
              os.environ['ipfsHash'] = str(ipfsHash[0]);
              os.environ['type']     = '2';
           elif (testType == 'gdrive'):
              os.environ['ipfsHash'] = str(ipfsHash[0]);
              os.environ['type']     = '4';

           ipfsHash = ipfsHashNo[counter].split(" ");

           os.environ['coreNum']  = ipfsHash[2];
           os.environ['desc']     = "science";

           if eudatFlag == 0:
              val = int(math.ceil(float(ipfsHash[1]) / 60));           
              log("RunTimeInMinutes: " + str(val), path)
              os.environ['runTime']  = str(val);
           else:
              log("RunTimeInMinutes: " + '360', path)
              os.environ['runTime']   = "360" # 6 hours for nasEUDAT simulation test.
           
           log("hash: " + ipfsHash[0] + "| TimeToRun: " + str(ipfsHash[1]) + "| Core:" + ipfsHash[2], path)

           account_id = randint(2,11);
           account_id = str(account_id);
           os.environ['accountID'] = account_id;
           # log(os.popen('echo /home/prc/eBlocBroker/contractCalls/submitJobTest.py $clusterID $ipfsHash $coreNum $desc $runTime $type $accountID 2>/dev/null').read().rstrip('\n'), path);          
           tx = os.popen('python /home/prc/eBlocBroker/contractCalls/submitJobTest.py $clusterID $ipfsHash $coreNum $desc $runTime $type $accountID 2>/dev/null').read().rstrip('\n');
           log(tx, path)

           txFile     = open(path + '/' + clusterID + '.txt', 'a');
           txFile.write(tx + " " + account_id + "\n");
           txFile.close();

           sleepSeconds = int(sleepTime);
           for remaining in range(sleepSeconds, 0, -1): #{
              sys.stdout.write("\r")
              sys.stdout.write("{:2d} seconds remaining...".format(remaining))
              sys.stdout.flush()
              time.sleep(1)
           #}

           sys.stdout.write("\rSleeping is done!\n")
           line1    = line2;
           line1_in = line2_in;
        else:
           skippedLines = skippedLines + 1;
    else: #{
       line1   = f.readline();
       line1_in = line1.split(" ")
    #}
    counter += 1;
  #}

  print("END");
  print(".");
  f.close();
#}
