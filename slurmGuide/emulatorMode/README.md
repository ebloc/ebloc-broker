# Slurm Emulator Mode Setup

https://slurm.schedmd.com/faq.html#multi_slurmd

```
git clone  https://github.com/SchedMD/slurm
cd slurm
./configure --enable-debug --enable-front-end
make install
```
/usr/local/etc/slurm.conf
/usr/local/etc/slurmdbd.conf
