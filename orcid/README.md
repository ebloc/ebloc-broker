# ORCID

tmux            (https://superuser.com/a/714465/723632)
tmux_cheatSheat (https://gist.github.com/henrik/1967800)

```
sudo killall cat

tmux new -s pipe1
bash orcidPipe.sh &
cntrl-B then D   or   exit 

tmux new -s pipe2
bash orcidPipe2.sh &
cntrl-B then D  or  exit

tmux attach # pipe2
```
