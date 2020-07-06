#!/bin/bash

# link:  https://stackoverflow.com/questions/5189560/squash-my-last-x-commits-together-using-git/5201642#5201642
git fetch
git reset --soft HEAD~1 # if HEAD~2 then it will squash latest 2 commits

message=$(git log --format=%B --reverse HEAD..HEAD@{1})
echo $message

git commit --edit -m $message
git push -f
