#!/bin/bash

# Adapted from 71529-ubucleaner.sh - http://www.opendesktop.org/CONTENT/content-files/71529-ubucleaner.sh
YELLOW="\033[1;33m"; RED="\033[0;31m"; NC="\033[0m"
OLDCONF=$(dpkg -l | grep "^rc" | awk '{print $2}')
LINUXPKG="linux-(image|headers|ubuntu-modules|restricted-modules)"
METALINUXPKG="linux-(image|headers|restricted-modules)-(generic|i386|server|common|rt|xen)"
if [ "$USER" != root ]; then
  echo -e $RED"Error: must be root! Exiting..."$NC
  exit 0
fi

echo -e $YELLOW"Cleaning apt ..."$NC
sudo apt-get autoremove blueman bluez-utils bluez bluetooth -y >/dev/null 2>&1
# sudo apt-get remove --purge libreoffice* -y >/dev/null 2>&1
sudo apt-get purge aisleriot gnome-sudoku mahjongg ace-of-penguins gnomine gbrainy -y >/dev/null 2>&1
sudo aptitude clean
sudo apt-get clean -y
sudo apt-get autoremove -y
sudo apt-get autoclean -y

if [ "$OLDCONF" != "" ]; then
    echo -e $YELLOW"Those packages were uninstalled without --purge:"$NC
    echo $OLDCONF
    #apt-get purge "$OLDCONF"  # fixes the error in the original script
    for PKGNAME in $OLDCONF ; do  # a better way to handle errors
        echo -e $YELLOW"Purge package $PKGNAME"
        apt-cache show "$PKGNAME" | grep Description: -A3
        apt-get -y purge "$PKGNAME"
    done
fi

echo -e $YELLOW"Emptying every trashes..."$NC
rm -rf ~/*/.local/share/Trash/*/** &> /dev/null
rm -rf /root/.local/share/Trash/*/** &> /dev/null
echo -e $YELLOW"Script Finished!"$NC
