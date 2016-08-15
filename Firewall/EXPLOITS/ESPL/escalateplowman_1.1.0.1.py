#!/usr/bin/env python

import os
import sys
import warnings

from params import *
from workit import *


#
# MAIN: setup params and call for real work
#
if __name__ == "__main__":
    # py2.3 emits curious warning
    warnings.filterwarnings("ignore", category=FutureWarning, append=1)

    # setup based on args
    params = Params()
    params.parse()
    params.display()

    command = prepare_command(params)
    if command:
        print "command ready:"
        print "===\n" + command + "\n==="
    else:
        print "problem building command, aborting"
        sys.exit(1)
