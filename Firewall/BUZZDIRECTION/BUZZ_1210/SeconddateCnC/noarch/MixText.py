#!/usr/bin/python

"""
This is a python implementation of the core
MixText functionality.  This is originally intended
to be used with BinStore to allow any machine to configure
BinStore enabled implants.
"""

import sys

MIX_TEXT_KEY_BYTE=0x47

def mix(src, rand):
    global MIX_TEXT_KEY_BYTE
    prev = ""
    retval = ""
    i = 0

    rand &= 0xff
    
    prev = (i ^ rand ^ MIX_TEXT_KEY_BYTE)
    retval += chr(prev)
    i += 1

    for char in src:
        c = ord(char)
        value = (c ^ (i ^ prev ^ MIX_TEXT_KEY_BYTE)) & 0xff
        retval += chr(value)
        prev += value
        prev &= 0xff
        i += 1        
        
        
    return retval

def unmix(src):
    global MIX_TEXT_KEY_BYTE
    i = 0
    retval = ""
    
    prev = ord(src[i])
    i += 1

    for char in src[i:]:
        c = ord(char)
        value = (c ^ MIX_TEXT_KEY_BYTE ^ prev ^ i) & 0xff
        retval += chr(value)
        prev += c
        prev &= 0xff
        i += 1
        
    return retval

def printBytes(string):
    for c in string:
        sys.stdout.write("%02x " % ord(c))
    sys.stdout.write("\n")


if __name__ == "__main__":
    # some real basic "unit testing"
    
    string = "\xff\xfe\x43\x00"

    print "original string:"
    printBytes(string)
    
    result = mix(string, 0x24)

    if len(result) != len(string) + 1:
        raise Exception, "mix'd strings should be one byte bigger"

    print "mix'd string: "
    printBytes(result)

    result2 = unmix(result)

    print "unmix'd string: "
    printBytes(result2)

    if result2 != string:
        raise Exception, "unmixing did not return original input"
    
