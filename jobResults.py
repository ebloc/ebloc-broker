import os, constants;

# Paths---------
eblocPath        = constants.EBLOCPATH;
contractCallPath = constants.EBLOCPATH + '/contractCalls'; os.environ['contractCallPath'] = contractCallPath;
fname = constants.LOG_PATH + '/queuedJobs.txt';
# ---------------

sum1=0;
counter = 1;
with open(fname, "r") as ins:
    array = []
    for line in ins:
        #print(line.rstrip('\n'))
        #array.append(line);

        res=line.split(' ')

        os.environ['clusterID'] = res[1];
        os.environ['jobKey']    = res[2];
        os.environ['index']     = res[3];

	sum1 += (int(res[7]) - int(res[8]))

        jobInfo = os.popen('python $contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];             
        r=jobInfo.split(',')

        print(str(counter) + " " + res[1] + " " + res[2] + " " + res[3] + " | " + constants.job_state_code[r[0]] + "," + r[1] + "," + r[2] + "," + r[3] + "," + r[4] + "," + r[5]);
        counter = counter + 1;

print(counter)            
print("GAINED: " + str(sum1));
