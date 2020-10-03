# Provider

Version of slurmctld should be same between frontend node and compute nodes.

Solution: munge key must be identical both in master and computing nodes.

```
SlurmctldPort=3002   => Controllers that port should be open.
SlurmdPort=6821      => Compute nodes all that port should be open.

id -u username
pkill -U UID
sudo usermod -u 1000 username
```
