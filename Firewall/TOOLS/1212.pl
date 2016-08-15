#!/usr/bin/perl

build_byte_table();

if (scalar(@ARGV)==1 && -f (my $filename=$ARGV[0]))
{
	open (IN,"$filename");
	while (my $line=<IN>)
	{
		print hextoIP($line);
		print "\n";			
	
	}
	close IN;
	exit 0;
}

elsif (scalar(@ARGV==1))
{
	print hextoIP($ARGV[0]);
	print "\n";
	exit 0;
}
elsif(scalar(@ARGV>1))
{
	print "ERROR: the filename or hex representation needs to be one argument try using \"'s\n";
	exit 0;
}
else
{
	while (my $line=<STDIN>)
	{
		print parseLine($line);
		print "\n\n";			
	
	}

return 0;

}







sub build_byte_table
{
%byte_table={};

my %table;
	my @chars=("0","1","2","3","4","5","6","7","8","9","a","b","c","d","e","f");
	
	for (my $i=0;$i<256;$i++)
	{
	$ones = $i % 16;
	$sixteens = ($i-$ones) / 16;
	
	$byte_table{"$chars[$sixteens]$chars[$ones]"}=$i;
	

	}
	

}

sub parseLine
{
my $line=$_[0];
my $ans="";
my $srcip;
my $dstip;
my $srcport;
my $dstport;
chomp $line;
$line=lc($line);
$line=~s/ //g;
#if (!(($srcip,$dstip,$srcport,$dstport) = ($line=~/^([a-f0-9]{4})([a-f0-9]{4})([a-f0-9]{2})([a-f0-9]{2})$/)))
if (!(($srcip,$dstip,$srcport,$dstport) = ($line=~/^([a-f0-9]{8})([a-f0-9]{8})([a-f0-9]{4})([a-f0-9]{4})$/)))
{
	return "ERROR: can't parse $line";
}
$srcip=hextoIP($srcip);
$dstip=hextoIP($dstip);
$dstport=hextoPort($dstport);
$srcport=hextoPort($srcport);
$ans="$srcip:$srcport -> $dstip:$dstport";
return $ans;
}


sub hextoPort
{
	

	my $line=$_[0];
	my $ans=0;
	chomp $line;
	$line=lc($line);
	$line=~s/ //g;
	if (!($line=~/^[a-f0-9]{4}$/))
	{
		return "ERROR:$line is not a valid port";
	}

	my $tempi=0;
	
	for (my $i=0;$i<(length($line)/2);$i++)
	{
		$ans=$ans*256;
		
		$tempi=substr($line,2*$i,2);
		$ans=$ans+$byte_table{$tempi};
		
	}
return $ans;
	


}

sub hextoIP
{
	

	my $line=$_[0];
	my $ans="";
	my @octets=();
	chomp $line;
	$line=lc($line);
	$line=~s/ //g;
	if (!($line=~/^(:?[a-f0-9]{2}){4}$/))
	{
		return "ERROR:$line is not a valid address";
	}

	my $tempi=0;
	
	for (my $i=0;$i<(length($line)/2);$i++)
	{
		
		$tempi=substr($line,2*$i,2);
		push(@octets,$byte_table{$tempi});
		
	}

	$ans=join(".",@octets);	


}
