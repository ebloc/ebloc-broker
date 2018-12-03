# Condor Setup

## Condor Install:

### Ubuntu: https://research.cs.wisc.edu/htcondor/instructions/ubuntu/14/stable/

```
wget -qO - https://research.cs.wisc.edu/htcondor/ubuntu/HTCondor-Release.gpg.key | sudo apt-key add -
# echo "deb http://research.cs.wisc.edu/htcondor/ubuntu/stable/ trusty contrib" >> /etc/apt/sources.list
sudo apt-get update
sudo apt-get install condor

## If error occurs do following:
sudo dpkg -i --force-overwrite /var/cache/apt/archives/condor_8.6.13-453497-ubuntu14_amd64.deb
sudo apt -f install

$ condor_version
$CondorVersion: 8.6.13 Oct 30 2018 BuildID: 453497 $
$CondorPlatform: x86_64_Ubuntu14 $
```

--------------

Link: https://stackoverflow.com/a/53029436/2402577

```
mkdir -p /var/run/condor  # If it does not exist
mkdir -p /var/lock/condor # If it does not exist

# Recreate them from scratch
sudo rm -rf /var/lib/condor
sudo mkdir -p /var/lib/condor/spool/local_univ_execute
sudo mkdir -p /var/lib/condor/execute
sudo chown -R condor: /var/lib/condor
sudo chmod 1777 /var/lib/condor/spool/local_univ_execute
sudo chmod 1777 /var/lib/condor/execute
	
mkdir -p /var/log/condor/
sudo chown -R condor: /var/log/condor
sudo chmod 1777 /var/log/condor

# Kill all the condor daemons you have running,
sudo service condor stop
sudo killall condor
sudo killall condor_procd

sudo service condor start # Condor should run as a system service. 

$ ps auxwwww | grep condor # You should see all processes run under condor.
condor      7656  0.0  0.2  47508  4644 ?        Ss   08:43   0:00 /usr/sbin/condor_master -pidfile /var/run/condor/condor.pid
root        7699  0.2  0.1  24384  3920 ?        S    08:43   0:00 condor_procd -A /var/run/condor/procd_pipe -L /var/log/condor/ProcLog -R 1000000 -S 60 -C 126
condor      7700  0.0  0.2  47004  5436 ?        Ss   08:43   0:00 condor_shared_port -f
condor      7701  0.1  0.3  57252  6620 ?        Ss   08:43   0:00 condor_collector -f
condor      7704  0.1  0.3  48352  6816 ?        Ss   08:43   0:00 condor_startd -f
condor      7705  0.0  0.3  58052  7188 ?        Ss   08:43   0:00 condor_schedd -f
condor      7706  0.0  0.2  47500  5880 ?        Ss   08:43   0:00 condor_negotiator -f

$ condor_q # check condor_q works or not
-- Schedd: condor@ebloc : <127.0.0.1:9618?... @ 10/26/18 08:46:06
OWNER BATCH_NAME      SUBMITTED   DONE   RUN    IDLE   HOLD  TOTAL JOB_IDS

0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended
```

-----------------

montage-workflow-v2: https://github.com/pegasus-isi/montage-workflow-v2

```
./example-dss.sh 

$ pegasus-run  /home/alper/pegasus/montage-workflow-v2/work/1540532824
Submitting to condor montage-0.dag.condor.sub
Submitting job(s).
1 job(s) submitted to cluster 1.

Your workflow has been started and is running in the base directory:

  /home/alper/pegasus/montage-workflow-v2/work/1540532824

*** To monitor the workflow you can run ***

  pegasus-status -l /home/alper/pegasus/montage-workflow-v2/work/1540532824

*** To remove your workflow run ***

  pegasus-remove /home/alper/pegasus/montage-workflow-v2/work/1540532824

$ pegasus-status -l /home/alper/pegasus/montage-workflow-v2/work/1540532824
STAT  IN_STATE  JOB
Run      04:21  montage-0 ( /home/alper/pegasus/montage-workflow-v2/work/1540532824 )
Run      00:51   ┣━merge_mProject_PID1_ID1
Run      00:31   ┣━merge_mProject_PID1_ID3
Run      00:31   ┣━merge_mProject_PID1_ID2
Run      00:11   ┗━merge_mProject_PID1_ID4
Summary: 5 Condor jobs total (R:5)

UNRDY READY   PRE  IN_Q  POST  DONE  FAIL %DONE STATE   DAGNAME
   46     0     0     4     0    10     0  16.7 Running *montage-0.dag
Summary: 1 DAG total (Running:1)

$ pegasus-status -l /home/alper/pegasus/montage-workflow-v2/work/1540532824
(no matching jobs found in Condor Q)
UNRDY READY   PRE  IN_Q  POST  DONE  FAIL %DONE STATE   DAGNAME
    0     0     0     0     0    60     0 100.0 Success *montage-0.dag
Summary: 1 DAG total (Success:1)
```
