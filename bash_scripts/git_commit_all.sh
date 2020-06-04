#!/bin/bash

clean.sh
FILE=bash_scripts/pre_commit.sh
if test -f "$FILE"; then
    ./bash_scripts/pre_commit.sh
fi

VAR1="c" # commit_right_away
while true; do
    if [ $# -eq 0 ]
    then
	read -p "#> Would you like to squash into the latest commit? [Y/n] exit [e]: " yn
    else
	yn=$1
    fi

    case $yn in
        [Yy]* )
	    git reset --soft HEAD~1
	    git add -A .
	    if [ -z "$2" ]
	    then # if second argument is not provided
		git commit --quiet --edit \
		    -m "$(git log --format=%B --reverse HEAD..HEAD@{1})" \
		    -m "$(cat ~/.git_commit_template.txt)"
		echo -e "Committed. Please wait few seconds for git to push"
	    else
		if [ "$2" = "$VAR1" ]; then
		    git commit --quiet -m "$(git log --format=%B --reverse HEAD..HEAD@{1})"
		    echo -e "Committed. Please wait few seconds for git to push"
		else
		    echo "Not committed"
		fi
	    fi

	    git push -f --quiet 2>&1 &
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
