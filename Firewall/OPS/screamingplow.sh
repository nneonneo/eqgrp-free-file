#!/bin/bash
#
# This script is used to configure Apache on your Opbox for FW Ops
#
# Change log: (Please mark changes here)
# 12/15/2010 - Script deployed
# 1/17/2012 - Added BG3100 and PBD support


echo "*****         Welcome to ScreamingPlow            *****"
echo "***** Please place your UA/PBD in /current/bin/FW/OPS *****"


echo "Select the version of BG"
echo "------------------------"
echo "1. BG3000"
echo "2. BG3100"
echo " "
echo -n "What is your selection: "
read _bgverselection

echo -n "What is the name of your UA: "
read _ua

case $_bgverselection in
        1 ) bgver=BG3000 ;;
        2 ) bgver=BG3100 
		echo -n "What is the name of your PBD: "
		read _pbd
		ln -s /current/bin/FW/OPS/$_pbd ../SCP/PBD_config.bin;;
        * ) echo "Invalid selection, bailing"
                exit 0;;
esac

cd /current/bin/FW/$bgver/Install/screamplow
ln -s ../SCP/* .
rm -f SCREAM_UA_full_support.bin
ln -s /current/bin/FW/OPS/$_ua SCREAM_UA_full_support.bin

ls -lart /current/bin/FW/$bgver/Install/screamplow

echo "You are now ready for a ScreamPlow"

