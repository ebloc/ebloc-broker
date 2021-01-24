# ORCID

tmux            (https://superuser.com/a/714465/723632)
tmux_cheatSheat (https://gist.github.com/henrik/1967800)

## Setup

```
sudo chmod 700 /eBloc
sudo setfacl -R -m user:alper:rwx    /eBloc
sudo setfacl -R -m user:www-data:rwx /eBloc
```

---------

```
sudo killall cat

tmux new -s pipe1
bash orcidPipeIn.sh &
cntrl-B then D # exit tmux window without quitting the terminal program
exit # to close 


tmux new -s pipe2
bash orcidPipeOut.sh &
cntrl-B then D # exit tmux window without quitting the terminal program
exit # to close 

To connect to tmux session:
tmux attach # pipe2
tmux attach # pipe2
```
