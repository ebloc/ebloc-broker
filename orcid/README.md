# ORCID

tmux            (https://superuser.com/a/714465/723632)
tmux_cheatSheat (https://gist.github.com/henrik/1967800)

```
sudo killall cat

tmux new -s pipe1
cat > /eBloc/fifo
cntrl-B then D

tmux new -s pipe2
cat /eBloc/fifo | xargs -I {} bash orcid.sh {}
cntrl-B then D


tmux attach # pipe2
```
