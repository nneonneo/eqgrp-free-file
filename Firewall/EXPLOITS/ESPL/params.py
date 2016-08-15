import sys
import optparse
import re

# configurable params:
#
#  download       (string)              parse to: dl_proto, dl_ip, dl_port, dl_file, dl_user, dl_pass
#  callback       ("30.40.50.60:9342")  parse to: callback_ip, callback_port
#  verbose
#  debug
#
# fallback defaults (set_defaults below)
# further overriden by cmdline options (optparse below)
#

class Params:
    def __init__(self):
        self.VERSION = "1.1.0.1"
        self.MY_NAME = "ESCALATEPLOWMAN"

        # build the parser
        self.parser = optparse.OptionParser(version="%prog " + self.VERSION,
                                            description=self.MY_NAME)

        self.parser.set_defaults(download     = "",
                                 dl_proto     = "",
                                 dl_ip        = "",
                                 dl_port      = "",
                                 dl_file      = "",
                                 dl_user      = "",
                                 dl_pass      = "",
                                 callback     = "",
                                 verbose      = True,
                                 debug        = False)

        self.parser.add_option("--download",
                               action="store", type="string", dest="download",
                               help="--download=ftp://user:pass@ip:port/file or --download=tftp://ip/file or --download=http://ip:port/file (REQUIRED)")

        self.parser.add_option("--callback",
                               action="store", type="string", dest="callback",
                               help="callback IP:port (REQUIRED)")

        self.parser.add_option("-v",
                               action="store_true", dest="verbose",
                               help="verbose mode (default)")
        self.parser.add_option("--debug",
                               action="store_true", dest="debug",
                               help="debug mode (for DEVS)")
        self.parser.add_option("-q",
                               action="store_false", dest="verbose",
                               help="quiet mode (suppress verbose)")

    def bail(self, msg):
        print "\n" + msg + "\n\n"
        self.parser.print_help()
        sys.exit(1)

    def parse(self):
        # parse 'em into options.*
        (options, args) = self.parser.parse_args(sys.argv)

        # review options.* and complain, copy good stuff to self.*/params.*
        host_pattern = "^\s*(\d+\.\d+\.\d+\.\d+):(\d+)\s*$"
        host_parser = re.compile(host_pattern)

        if not options.download:
            self.bail("require a --download option to specify ftp or tftp source")

        ftp_pattern = "^\s*ftp://([^:]+):([^:@]+)@(\d+\.\d+\.\d+\.\d+):(\d+)/(\S+)\s*$"
        tftp_pattern = "^\s*tftp://(\d+\.\d+\.\d+\.\d+)/(\S+)\s*$"
        http_pattern = "^\s*http://(\d+\.\d+\.\d+\.\d+):(\d+)/(\S+)\s*$"

        ftp_parser = re.compile(ftp_pattern)
        tftp_parser = re.compile(tftp_pattern)
        http_parser = re.compile(http_pattern)

        ftp_matches = ftp_parser.search(options.download)
        tftp_matches = tftp_parser.search(options.download)
        http_matches = http_parser.search(options.download)
        
        if ftp_matches:
            self.dl_proto = "ftp"
            self.dl_user = ftp_matches.group(1)
            self.dl_pass = ftp_matches.group(2)
            self.dl_ip = ftp_matches.group(3)
            self.dl_port = int(ftp_matches.group(4))
            self.dl_file = ftp_matches.group(5)
        elif tftp_matches:
            self.dl_proto = "tftp"
            self.dl_ip = tftp_matches.group(1)
            self.dl_file = tftp_matches.group(2)
        elif http_matches:
            self.dl_proto = "http"
            self.dl_ip = http_matches.group(1)
            self.dl_port = http_matches.group(2)
            self.dl_file = http_matches.group(3)
        else:
            self.bail("download option did not parse good: " + options.download)   

        if options.callback:
            matches = host_parser.search(options.callback)
            if matches:
                self.callback_ip = matches.group(1)
                self.callback_port = int(matches.group(2))
            else:
                self.bail(options.callback + " doesn't look like IP:port!")
        else:
            self.bail("--callback option is required")

        self.verbose = options.verbose
        self.debug = options.debug
        if self.debug:
            self.verbose = True  # debug implies verbose

    def display(self):
        print "==========================="
        print "%s (v%s) beginning..." % (self.MY_NAME, self.VERSION)
        if self.dl_proto == "ftp":
            print "using ftp to download file %s from IP:port %s:%d, user %s passwd %s" % (self.dl_file, self.dl_ip, self.dl_port, self.dl_user, self.dl_pass)
        elif self.dl_proto == "tftp":
            print "using tftp to download file %s from IP %s" % (self.dl_file, self.dl_ip)
        elif self.dl_proto == "http":
            print "using wget to download file %s from IP %s, port %s" % (self.dl_file, self.dl_ip, self.dl_port)
        print "callback: %s:%d" % (self.callback_ip, self.callback_port)
        if self.verbose:
            print "verbose mode ON"
        if self.debug:
            print "debug mode ON"
        print "==========================="
