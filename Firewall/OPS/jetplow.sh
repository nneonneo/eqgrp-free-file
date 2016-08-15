#!/bin/bash
#
# This script is used to configure Apache on your Opbox for FW Ops
#
# Change log: (Please mark changes here)
# 12/15/2010 - Script deployed



echo "*****             Welcome to JetPlow              *****"
echo "***** Please place your UA in /current/bin/FW/OPS *****"

echo "Select the version of BG"
echo "------------------------"
echo "1. BG2100"
echo "2. BG2200"
echo " "
echo -n "What is your selection: "
read _bgverselection

case $_bgverselection in
	1 ) bgver=BG2100 ;;
	2 ) bgver=BG2200 ;;
	* ) echo "Invalid selection, bailing"
		exit 0;;
esac


echo -n "What is the name of your UA: "
read _ua


cd /current/bin/FW/BANANAGLEE/$bgver/Install/LP/jetplow
ln -s ../jp/orig_ua.bin orig_bg_pixGen.bin
ln -s ../jp/orig_code.bin orig_code_pixGen.bin
ln -s ../jp/orig_hook.bin orig_hook_pixGen.bin
ln -s ../jp/jp11_hook_gen.bin hook_pixGen.bin
ln -s ../jp/jp11_code_pixGen.bin jp_code_pixGen.bin
ln -s /current/bin/FW/OPS/$_ua jp_ua_pixGen.bin

ls -lart "/current/bin/FW/$bgver/Install/LP/jetplow"


echo "You are now ready for a JP :)"


