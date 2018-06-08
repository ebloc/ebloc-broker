# ORCID

tmux            (https://superuser.com/a/714465/723632)
tmux_cheatSheat (https://gist.github.com/henrik/1967800)

## Setup

```
chmod 700 /eBloc
chown www-data /eBloc

sudo chown www-data /eBloc
sudo chown alper    /eBloc
```

---------

```
sudo killall cat

tmux new -s pipe1
bash orcidPipeIn.sh &
cntrl-B then D   or   exit 

tmux new -s pipe2
bash orcidPipeOut.sh &
cntrl-B then D  or exit

tmux attach # pipe2
```
