#!/usr/bin/perl
use Getopt::Long;

sub usage{

  print "\n\nclean_up_blobs.pl puts the correct implant version number into the\n\tblob files in the directory it is run.\n";

  print "Usage: clean_up_blobs.pl --ver <implant version> [-h]\n\n";
  print "	--ver <implant version>\n";
  print "	     Implant version should be of the form X.X.X.X  where 256 > X >= 0\n\n";
  print "	[-h]\n";
  print "	   print this usage statement\n\n";
};

GetOptions("ver=s");

if (!defined($opt_ver))
{
  usage();
  die;
}

printf "%s\n", $opt_ver;

if ( $opt_ver =~ /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/)
{
  if ( ($1 > 255) || ($2 > 255) || ($3 > 255) || ($4 > 255) )
  {
     usage();
     printf "Version numbers must be less than 256 and non-negative:  %s\n", $opt_ver;
     die;
  }

  open SEC_HALF, ">second_half";
  binmode SEC_HALF;
  printf SEC_HALF "%c%c%c%c", $4,$3,$2,$1;
}
else
{ 
  usage();
  printf "ERROR in version number:  %s\n", $opt_ver;
  die;
}

opendir THISDIR, "." or die "serious drainbamage: $!";

@allfiles = grep /\.blob$/, readdir THISDIR;

my $file;

foreach $file (@allfiles)
 {
   printf "working on $file\n";

   `dd if=$file of=first_half bs=1 count=36`;

   `dd if=$file of=third_half bs=1 skip=40`;

   `rm $file`;

   `cat first_half second_half third_half > $file`;

   `rm first_half third_half`;
 }

`rm second_half`;



