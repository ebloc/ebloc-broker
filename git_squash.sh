#!/bin/bash

# link:  https://stackoverflow.com/questions/5189560/squash-my-last-x-commits-together-using-git/5201642#5201642
git reset --soft HEAD~2
git commit --edit -m"$(git log --format=%B --reverse HEAD..HEAD@{1})"
git push -f
