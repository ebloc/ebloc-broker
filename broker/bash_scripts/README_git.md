# Git Guide

## Git Pull

### Update git repository with the origin/master

```
git fetch --all && git reset --hard origin/master
```

## How to save username and password in git

```
git config credential.helper store
```

then

```
git pull
```

## Also I suggest you to read:

```
git help credentials
```

### Git Undo

`git reflog`
Suppose the old commit was `HEAD@{5}` in the ref log:

```
git reset --hard HEAD@{5}
```

==> Actually, rebase saves your starting point to ORIG_HEAD so this is
usually as simple as:

`git reset --hard ORIG_HEAD`

## Git checkout into the latest commit

```
git fetch --dry-run
git fetch origin && git reset --hard origin/master


If you're making frequent small commits, then start by looking at the commit comments with `git log
--merge`. Then `git diff` will show you the conflicts.
