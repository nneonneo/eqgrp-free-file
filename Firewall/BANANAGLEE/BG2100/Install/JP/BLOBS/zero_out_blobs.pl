#!/usr/bin/perl

opendir THISDIR, "." or die "serious drainbamage: $!";

@allfiles = grep /\.blob$/, readdir THISDIR;

my $file;

`dd if=/dev/zero of=second_half bs=1 count=512`;

foreach $file (@allfiles)
 {
   printf "working on $file\n";

   `dd if=$file of=first_half bs=1 count=32`;

   `dd if=$file of=third_half bs=1 skip=544`;

   `rm $file`;

   `cat first_half second_half third_half > $file`;

   `rm first_half third_half`;
 }

`rm second_half`;



