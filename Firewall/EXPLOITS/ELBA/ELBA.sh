#!/bin/bash
#
# ELBA.sh - Interface to the ELBA program.
#

#
# If we don't have the executable then go no further.
#
if [ ! -e ELBA ]
then
	echo "Can't find executable: ELBA"
	
	exit 1
fi

#
# Print a usage message and exit.
#
usage() {
	echo "usage: $0 version [ options ]"
	
	echo "Currently supported versions:"
	echo "	v3.2.100.010"
	echo "	v3.3.001.050"
	echo "	v3.3.002.021"
	echo "	v3.3.002.030"
	echo "	vTEST"

	./ELBA

	echo "Ignore the \"-a\" option. This script inserts the address."
	
	exit 1
}

if [ $# -eq 0 ]
then
	usage
fi

case $1 in
	v3.2.100.010)
		HEAPADDR=0x083f6d40
		;;
		
	v3.3.001.050)
		HEAPADDR=0x0849bd78
		;;
		
	v3.3.002.021)
		HEAPADDR=0x0821e778
		;;
		
	v3.3.002.030)
		HEAPADDR=0x0821e778
		;;
		
	vTEST)
		HEAPADDR=0x083f4780
		;;
		
	*)
		echo "Unknown version: $1"
		usage
		;;
esac

#
# We have the address to use off the command line so shift out the version.
#
shift 

#
# Execute the command with all the specified options. Note the $@ MUST BE
# QUOTED to work correctly.
#
./ELBA -a $HEAPADDR "$@"

echo "ELBA exit status: $?"
