#!/bin/bash

GREEN="\033[1;32m"
NC="\033[0m" # No Color

base_dir=$(git rev-parse --show-toplevel)
if [ ! -d "$base_dir" ]; then
    echo "base git directory does not exist, exited."
    exit
fi
current_dir=$PWD

$HOME/eBlocBroker/bash_scripts/clean.sh
# pre-commit autoupdate
if [[ $PWD =~ "eBlocBroker" ]]
then
    SKIP=mypy pre-commit run --all-files
fi
git fetch

arg=$#
VAR1="c" # commit_right_away: gc y c
while true; do
    if [ $# -eq 0 ]
    then
	echo ""
	read -p "#> Would you like to squash into the latest commit? [Y/n] exit [e]: " yn
    else
	arg=0
	yn=$1
    fi

    case $yn in
        [Yy]* )
	    cd $base_dir
	    git reset --soft HEAD~1
	    git add -A .
	    if [ -z "$2" ]
	    then # if second argument is not provided
		git commit --no-verify --quiet --edit \
		    -m "$(git log --format=%B --reverse HEAD..HEAD@{1})" \
		    -m "$(cat ~/.git_commit_template.txt)"
		echo -e "Committed. Please wait few seconds for git to push"
	    else
		if [ "$2" = "$VAR1" ]; then
		    git commit --no-verify --quiet -m "$(git log --format=%B --reverse HEAD..HEAD@{1})"
		    echo -e "${GREEN}Committed. Please wait few seconds for git to push${NC}"
		else
		    echo "Not committed"
		fi
	    fi
	    git push -f --quiet 2>&1 &
	    cd $current_dir
	    exit
	    ;;
        [Nn]* )
	    git add -A .
	    git commit --quiet
	    git push -f --quiet 2>&1 &
	    exit
	    ;;
	[Ee]* )
	    echo "exit"
	    exit
	    ;;
        * )
	    echo "exit"
	    exit
	    ;;
    esac
done
