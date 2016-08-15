#!/usr/bin/python

"""
This is wrapper for Store.py that FELONYCROWBAR will use. This
program takes an xml file as input.  This xml file will contain
a series of configuration name value pairs.  The xml file is in
this format (quotes escaped for inclusion in this comment block):

<BinStoreConfig>
    <ConfigItem name=\"myname1\" value=\"myvalue1\"/>
    <ConfigItem name=\"myname2\" value=\"myvalue2\"/>
    <ConfigItem name=\"myname3\" valueFromFile=\"/tmp/filevalue.bin\"/>
    <ConfigItem name=\"myname4\" valueFromHex=\"6639713c0f85998120193543fe9a8411\"/>
</BinStoreConfig>

For most implants the only thing that will be required is the name/value
construct.  If you need to store binary data (i.e. non-strings) then you
will need to use the valueFromFile attribute.  This reads the config value
from a file without modification (i.e. it does not null terminate the data).
You can also use the valueFromHex attribute to encode binary data (as a HEX string)
into the configuration variable, this allows you to store small binary blobs without
writing them to an external file.
"""

import sys
import getopt
import binascii
from xml.parsers import expat
import Store


USAGE="""
Usage: StoreFc.py --configFile=<path to xml file> --implantFile=<path to BinStore implant> [--outputFile=<file to write the configured implant to>]
"""

"""
Very simple xml parser. Creates a dictionary of config values
from an xml file.
"""
class ConfigParser(object):
   
    def __init__(self, filename):
        self.configMap = { }
        parser = expat.ParserCreate( )
        parser.StartElementHandler = self.StartElement
        
        f = open(filename, 'rb')
        xmlBuf = f.read( )
        
        parserStatus = parser.Parse(xmlBuf, 1)
        
    def StartElement(self, name, atts):
        if name == 'BinStoreConfig':
            return
        
        if name != 'ConfigItem':
            raise Exception, "Do not know how to parse element %s" % name

        if not atts.has_key('name'):
            raise Exception, "configItem element must have a name attribute."

        if not ( atts.has_key('value') or
                 atts.has_key('valueFromFile') or
                 atts.has_key('valueFromHex') ):
            raise Exception, (
                "configItem element must have either a value, valueFromFile, or valuFromHex  attribute")
        
        name = atts['name']
        if atts.has_key('value'):
            value = atts['value']
            value += '\x00'
        elif atts.has_key('valueFromFile'):
            filename = atts['valueFromFile']
            f = open(filename, 'rb')
            value = f.read( )
            f.close( )
        elif atts.has_key('valueFromHex'):
            value = binascii.a2b_hex(atts['valueFromHex'])

        self.configMap[name] = value


    def getResult(self):
        return self.configMap


def main( ):

    if len(sys.argv) < 3:
        print "Must supply arguments."
        print USAGE
        sys.exit(-1)

    try:
        (opts, args) = getopt.getopt(
            sys.argv[1:],
            "",
            ["configFile=",
             "implantFile=",
             "outputFile="])
    except getopt.GetoptError, err:
        print str(err)
        print USAGE
        sys.exit(-1)

    oConfigFilename = None
    oImplantFilename = None
    oOutputFilename = None
    
    for option, value in opts:
        if option == "--configFile":
            oConfigFilename = value
        elif option == "--implantFile":
            oImplantFilename = value
        elif option == "--outputFile":
            oOutputFilename = value

    if oConfigFilename == None or oImplantFilename == None:
        raise Exception, "Must supply both a config file and implant file."

    config = ConfigParser(oConfigFilename)

    f = open(oImplantFilename, 'rb')
    fileBuf = f.read( )
    f.close( )

    fileBuf = Store.wipe(fileBuf)
    fileBuf = Store.setValues(fileBuf, config.getResult( ))

    if oOutputFilename == None:
        f = open(oImplantFilename, 'wb')
    else:
        f = open(oOutputFilename, 'wb')
        
    f.write(fileBuf)
    f.close( )
    
if __name__ == "__main__":
    main( )
