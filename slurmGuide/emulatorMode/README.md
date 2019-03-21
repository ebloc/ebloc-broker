# Slurm Emulator Mode Setup

https://slurm.schedmd.com/faq.html#multi_slurmd

```
git clone  https://github.com/SchedMD/slurm
cd slurm
./configure --enable-debug --enable-front-end
sudo make install
```

## Required files to be updated

```
sudo emacs -nw /usr/local/etc/slurm.conf
sudo emacs -nw /usr/local/etc/slurmdbd.conf
```
