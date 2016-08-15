

def hexdump(str, x):
    for i in xrange(0, len(str)):
	if i % x == 0:
	    print "0x%08x: " % (i),
        print "%02x" % (ord(str[i])),
        if i % x == x - 1 or i == len(str) - 1:
            print
