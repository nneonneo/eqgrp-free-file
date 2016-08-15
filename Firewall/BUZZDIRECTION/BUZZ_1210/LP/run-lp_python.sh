#!/bin/bash

if [ $# -lt 1 ]
then
    echo "Incorrect number of input arguments.  Use -help for usage information."
    exit
elif [ $1 = '--help' ] || [ $1 = '-help' ] || [ $1 = '-h' ] || [ $1 = '--h' ]
then
    echo
    echo "Usage: run-lp_python.sh --lp <LP IP address> --implant <Implant IP address> --sport <Source port> --dport <Destination Port> --key <path to keyfile> [--rotate <0|1>]"
    echo "Optional Arguments:"
    echo "    --rotate <0|1>"
    echo "      Determines whether or not lp logs will be rotated.  If rotate is 1, a" 
    echo "      maximum of 20 logs will be stored.  If rotate is 0, the number of"
    echo "      stored log files will not be limited." 
    echo "      If not provided, this argument will default to 0."        
    echo
    exit
elif [ $# -lt 10 ] || [ $# -gt 12 ] || [ $# -eq 11 ]
then
    echo "Incorrect number of input arguments.  Use -help for usage information."
    exit
fi

lpIp=' '
implantIp=' '
sPort=' '
dPort=' '
keyFile=' '
rotateLogs='0'

for arg in "$@"
do
    args[$i]=$arg
    let i=${i}+1
done

for ((i1=0;i1<$#;i1++))
do
    if [ ${args[i1]} = "--lp" ]
    then
        lpIp=${args[i1+1]}
    elif [ ${args[i1]} = "--implant" ]
    then
        implantIp=${args[i1+1]}
    elif [ ${args[i1]} = "--sport" ]
    then
        sPort=${args[i1+1]}
    elif [ ${args[i1]} = "--dport" ]
    then
        dPort=${args[i1+1]}
    elif [ ${args[i1]} = "--key" ]
    then
        keyFile=${args[i1+1]}
    elif [ ${args[i1]} = "--rotate" ]
    then
        rotateLogs=${args[i1+1]}
    fi
done

if [ "$lpIp" = ' ' ] 
then
    echo
    echo "Missing argument: lp"
    echo "Use -h for usage information."
    exit
elif [ "$implantIp" = ' ' ] 
then
    echo
    echo "Missing argument: implant"
    echo "Use -h for usage information."
    exit
elif [ "$sPort" = ' ' ] 
then
    echo
    echo "Missing argument: sport"
    echo "Use -h for usage information."
    exit
elif [ "$dPort" = ' ' ] 
then
    echo
    echo "Missing argument: dport"
    echo "Use -h for usage information."
    exit
elif [ "$keyFile" = ' ' ] 
then
    echo
    echo "Missing argument: key"
    echo "Use -h for usage information."
    exit
fi

echo "Go Time!"

python Scripts/Lp_UserInterface.py $implantIp $dPort $lpIp $sPort $keyFile $rotateLogs

exec 2> /dev/null

killall Backend.lp
jobs -p | xargs -n 1 kill
