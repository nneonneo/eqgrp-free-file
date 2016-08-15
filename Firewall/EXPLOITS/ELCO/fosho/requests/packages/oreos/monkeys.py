# -*- coding: utf-8 -*-

"""
oreos.monkeys
~~~~~~~~~~~~~

Monkeypatches.
"""
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


r"""
Here's a sample session to show how to use this module.
At the moment, this is the only documentation.

The Basics
----------

Importing is easy..

   >>> import Cookie

Most of the time you start by creating a cookie.  Cookies come in
three flavors, each with slightly different encoding semantics, but
more on that later.

   >>> C = Cookie.SimpleCookie()
   >>> C = Cookie.SerialCookie()
   >>> C = Cookie.SmartCookie()

[Note: Long-time users of Cookie.py will remember using
Cookie.Cookie() to create an Cookie object.  Although deprecated, it
is still supported by the code.  See the Backward Compatibility notes
for more information.]

Once you've created your Cookie, you can add values just as if it were
a dictionary.

   >>> C = Cookie.SmartCookie()
   >>> C["fig"] = "newton"
   >>> C["sugar"] = "wafer"
   >>> C.output()
   'Set-Cookie: fig=newton\r\nSet-Cookie: sugar=wafer'

Notice that the printable representation of a Cookie is the
appropriate format for a Set-Cookie: header.  This is the
default behavior.  You can change the header and printed
attributes by using the .output() function

   >>> C = Cookie.SmartCookie()
   >>> C["rocky"] = "road"
   >>> C["rocky"]["path"] = "/cookie"
   >>> print C.output(header="Cookie:")
   Cookie: rocky=road; Path=/cookie
   >>> print C.output(attrs=[], header="Cookie:")
   Cookie: rocky=road

The load() method of a Cookie extracts cookies from a string.  In a
CGI script, you would use this method to extract the cookies from the
HTTP_COOKIE environment variable.

   >>> C = Cookie.SmartCookie()
   >>> C.load("chips=ahoy; vienna=finger")
   >>> C.output()
   'Set-Cookie: chips=ahoy\r\nSet-Cookie: vienna=finger'

The load() method is darn-tootin smart about identifying cookies
within a string.  Escaped quotation marks, nested semicolons, and other
such trickeries do not confuse it.

   >>> C = Cookie.SmartCookie()
   >>> C.load('keebler="E=everybody; L=\\"Loves\\"; fudge=\\012;";')
   >>> print C
   Set-Cookie: keebler="E=everybody; L=\"Loves\"; fudge=\012;"

Each element of the Cookie also supports all of the RFC 2109
Cookie attributes.  Here's an example which sets the Path
attribute.

   >>> C = Cookie.SmartCookie()
   >>> C["oreo"] = "doublestuff"
   >>> C["oreo"]["path"] = "/"
   >>> print C
   Set-Cookie: oreo=doublestuff; Path=/

Each dictionary element has a 'value' attribute, which gives you
back the value associated with the key.

   >>> C = Cookie.SmartCookie()
   >>> C["twix"] = "none for you"
   >>> C["twix"].value
   'none for you'


A Bit More Advanced
-------------------

As mentioned before, there are three different flavors of Cookie
objects, each with different encoding/decoding semantics.  This
section briefly discusses the differences.

SimpleCookie

The SimpleCookie expects that all values should be standard strings.
Just to be sure, SimpleCookie invokes the str() builtin to convert
the value to a string, when the values are set dictionary-style.

   >>> C = Cookie.SimpleCookie()
   >>> C["number"] = 7
   >>> C["string"] = "seven"
   >>> C["number"].value
   '7'
   >>> C["string"].value
   'seven'
   >>> C.output()
   'Set-Cookie: number=7\r\nSet-Cookie: string=seven'


SerialCookie

The SerialCookie expects that all values should be serialized using
cPickle (or pickle, if cPickle isn't available).  As a result of
serializing, SerialCookie can save almost any Python object to a
value, and recover the exact same object when the cookie has been
returned.  (SerialCookie can yield some strange-looking cookie
values, however.)

   >>> C = Cookie.SerialCookie()
   >>> C["number"] = 7
   >>> C["string"] = "seven"
   >>> C["number"].value
   7
   >>> C["string"].value
   'seven'
   >>> C.output()
   'Set-Cookie: number="I7\\012."\r\nSet-Cookie: string="S\'seven\'\\012p1\\012."'

Be warned, however, if SerialCookie cannot de-serialize a value (because
it isn't a valid pickle'd object), IT WILL RAISE AN EXCEPTION.


SmartCookie

The SmartCookie combines aspects of each of the other two flavors.
When setting a value in a dictionary-fashion, the SmartCookie will
serialize (ala cPickle) the value *if and only if* it isn't a
Python string.  String objects are *not* serialized.  Similarly,
when the load() method parses out values, it attempts to de-serialize
the value.  If it fails, then it fallsback to treating the value
as a string.

   >>> C = Cookie.SmartCookie()
   >>> C["number"] = 7
   >>> C["string"] = "seven"
   >>> C["number"].value
   7
   >>> C["string"].value
   'seven'
   >>> C.output()
   'Set-Cookie: number="I7\\012."\r\nSet-Cookie: string=seven'


Backwards Compatibility
-----------------------

In order to keep compatibilty with earlier versions of Cookie.py,
it is still possible to use Cookie.Cookie() to create a Cookie.  In
fact, this simply returns a SmartCookie.

   >>> C = Cookie.Cookie()
   >>> print C.__class__.__name__
   SmartCookie


Finis.
"""  ##

##

##


##

##

##

import string

try:
    from cPickle import dumps, loads
except ImportError:
    from pickle import dumps, loads

import re, warnings

__all__ = ["CookieError","BaseCookie","SimpleCookie","SerialCookie",
           "SmartCookie","Cookie"]

_nulljoin = ''.join
_semispacejoin = '; '.join
_spacejoin = ' '.join

##

##

##

class CookieError(Exception):
    pass


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

_RFC2965Forbidden = "[]:{}="
_LegalChars       = ( string.ascii_letters + string.digits + 
                      "!#$%&'*+-.^_`|~_@" + _RFC2965Forbidden )
_Translator       = {
    '\000' : '\\000',  '\001' : '\\001',  '\002' : '\\002',
    '\003' : '\\003',  '\004' : '\\004',  '\005' : '\\005',
    '\006' : '\\006',  '\007' : '\\007',  '\010' : '\\010',
    '\011' : '\\011',  '\012' : '\\012',  '\013' : '\\013',
    '\014' : '\\014',  '\015' : '\\015',  '\016' : '\\016',
    '\017' : '\\017',  '\020' : '\\020',  '\021' : '\\021',
    '\022' : '\\022',  '\023' : '\\023',  '\024' : '\\024',
    '\025' : '\\025',  '\026' : '\\026',  '\027' : '\\027',
    '\030' : '\\030',  '\031' : '\\031',  '\032' : '\\032',
    '\033' : '\\033',  '\034' : '\\034',  '\035' : '\\035',
    '\036' : '\\036',  '\037' : '\\037',

    ##

    ##


    ',' : '\\054', ';' : '\\073',

    '"' : '\\"',       '\\' : '\\\\',

    '\177' : '\\177',  '\200' : '\\200',  '\201' : '\\201',
    '\202' : '\\202',  '\203' : '\\203',  '\204' : '\\204',
    '\205' : '\\205',  '\206' : '\\206',  '\207' : '\\207',
    '\210' : '\\210',  '\211' : '\\211',  '\212' : '\\212',
    '\213' : '\\213',  '\214' : '\\214',  '\215' : '\\215',
    '\216' : '\\216',  '\217' : '\\217',  '\220' : '\\220',
    '\221' : '\\221',  '\222' : '\\222',  '\223' : '\\223',
    '\224' : '\\224',  '\225' : '\\225',  '\226' : '\\226',
    '\227' : '\\227',  '\230' : '\\230',  '\231' : '\\231',
    '\232' : '\\232',  '\233' : '\\233',  '\234' : '\\234',
    '\235' : '\\235',  '\236' : '\\236',  '\237' : '\\237',
    '\240' : '\\240',  '\241' : '\\241',  '\242' : '\\242',
    '\243' : '\\243',  '\244' : '\\244',  '\245' : '\\245',
    '\246' : '\\246',  '\247' : '\\247',  '\250' : '\\250',
    '\251' : '\\251',  '\252' : '\\252',  '\253' : '\\253',
    '\254' : '\\254',  '\255' : '\\255',  '\256' : '\\256',
    '\257' : '\\257',  '\260' : '\\260',  '\261' : '\\261',
    '\262' : '\\262',  '\263' : '\\263',  '\264' : '\\264',
    '\265' : '\\265',  '\266' : '\\266',  '\267' : '\\267',
    '\270' : '\\270',  '\271' : '\\271',  '\272' : '\\272',
    '\273' : '\\273',  '\274' : '\\274',  '\275' : '\\275',
    '\276' : '\\276',  '\277' : '\\277',  '\300' : '\\300',
    '\301' : '\\301',  '\302' : '\\302',  '\303' : '\\303',
    '\304' : '\\304',  '\305' : '\\305',  '\306' : '\\306',
    '\307' : '\\307',  '\310' : '\\310',  '\311' : '\\311',
    '\312' : '\\312',  '\313' : '\\313',  '\314' : '\\314',
    '\315' : '\\315',  '\316' : '\\316',  '\317' : '\\317',
    '\320' : '\\320',  '\321' : '\\321',  '\322' : '\\322',
    '\323' : '\\323',  '\324' : '\\324',  '\325' : '\\325',
    '\326' : '\\326',  '\327' : '\\327',  '\330' : '\\330',
    '\331' : '\\331',  '\332' : '\\332',  '\333' : '\\333',
    '\334' : '\\334',  '\335' : '\\335',  '\336' : '\\336',
    '\337' : '\\337',  '\340' : '\\340',  '\341' : '\\341',
    '\342' : '\\342',  '\343' : '\\343',  '\344' : '\\344',
    '\345' : '\\345',  '\346' : '\\346',  '\347' : '\\347',
    '\350' : '\\350',  '\351' : '\\351',  '\352' : '\\352',
    '\353' : '\\353',  '\354' : '\\354',  '\355' : '\\355',
    '\356' : '\\356',  '\357' : '\\357',  '\360' : '\\360',
    '\361' : '\\361',  '\362' : '\\362',  '\363' : '\\363',
    '\364' : '\\364',  '\365' : '\\365',  '\366' : '\\366',
    '\367' : '\\367',  '\370' : '\\370',  '\371' : '\\371',
    '\372' : '\\372',  '\373' : '\\373',  '\374' : '\\374',
    '\375' : '\\375',  '\376' : '\\376',  '\377' : '\\377'
    }

_idmap = ''.join(chr(x) for x in range(256))

def _quote(str, LegalChars=_LegalChars,
           idmap=_idmap, translate=string.translate):
    ##

    ##

    ##

    ##

    ##

    ##

    if "" == translate(str, idmap, LegalChars):
        return str
    else:
        return '"' + _nulljoin( map(_Translator.get, str, str) ) + '"'
##



_OctalPatt = re.compile(r"\\[0-3][0-7][0-7]")
_QuotePatt = re.compile(r"[\\].")

def _unquote(str):
    ##

    ##

    if  len(str) < 2:
        return str
    if str[0] != '"' or str[-1] != '"':
        return str

    ##

    ##


    ##

    str = str[1:-1]

    ##

    ##

    ##

    ##

    i = 0
    n = len(str)
    res = []
    while 0 <= i < n:
        Omatch = _OctalPatt.search(str, i)
        Qmatch = _QuotePatt.search(str, i)
        if not Omatch and not Qmatch:              ##

            res.append(str[i:])
            break
        ##

        j = k = -1
        if Omatch: j = Omatch.start(0)
        if Qmatch: k = Qmatch.start(0)
        if Qmatch and ( not Omatch or k < j ):     ##

            res.append(str[i:k])
            res.append(str[k+1])
            i = k+2
        else:                                      ##

            res.append(str[i:j])
            res.append( chr( int(str[j+1:j+4], 8) ) )
            i = j+4
    return _nulljoin(res)
##


##

##

##

##

##

##

##


_weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

_monthname = [None,
              'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def _getdate(future=0, weekdayname=_weekdayname, monthname=_monthname):
    from time import gmtime, time
    now = time()
    year, month, day, hh, mm, ss, wd, y, z = gmtime(now + future)
    return "%s, %02d-%3s-%4d %02d:%02d:%02d GMT" %           (weekdayname[wd], day, monthname[month], year, hh, mm, ss)


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


class Morsel(dict):
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

    _reserved = { "expires" : "expires",
                   "path"        : "Path",
                   "comment" : "Comment",
                   "domain"      : "Domain",
                   "max-age" : "Max-Age",
                   "secure"      : "secure",
                   "httponly"  : "httponly",
                   "version" : "Version",
                   }

    def __init__(self):
        ##

        self.key = self.value = self.coded_value = None

        ##

        for K in self._reserved:
            dict.__setitem__(self, K, "")
    ##


    def __setitem__(self, K, V):
        K = K.lower()
        if not K in self._reserved:
            raise CookieError("Invalid Attribute %s" % K)
        dict.__setitem__(self, K, V)
    ##


    def isReservedKey(self, K):
        return K.lower() in self._reserved
    ##


    def set(self, key, val, coded_val,
            LegalChars=_LegalChars,
            idmap=_idmap, translate=string.translate):
        ##

        ##

        if key.lower() in self._reserved:
            raise CookieError("Attempt to set a reserved key: %s" % key)
        if "" != translate(key, idmap, LegalChars):
            raise CookieError("Illegal key value: %s" % key)

        ##

        self.key                 = key
        self.value               = val
        self.coded_value         = coded_val
    ##


    def output(self, attrs=None, header = "Set-Cookie:"):
        return "%s %s" % ( header, self.OutputString(attrs) )

    __str__ = output

    def __repr__(self):
        return '<%s: %s=%s>' % (self.__class__.__name__,
                                self.key, repr(self.value) )

    def js_output(self, attrs=None):
        ##

        return """
        <script type="text/javascript">
        <!-- begin hiding
        document.cookie = \"%s\";
        // end hiding -->
        </script>
        """ % ( self.OutputString(attrs).replace('"',r'\"'), )
    ##


    def OutputString(self, attrs=None):
        ##

        ##

        result = []
        RA = result.append

        ##

        RA("%s=%s" % (self.key, self.coded_value))

        ##

        if attrs is None:
            attrs = self._reserved
        items = self.items()
        items.sort()
        for K,V in items:
            if V == "": continue
            if K not in attrs: continue
            if K == "expires" and type(V) == type(1):
                RA("%s=%s" % (self._reserved[K], _getdate(V)))
            elif K == "max-age" and type(V) == type(1):
                RA("%s=%d" % (self._reserved[K], V))
            elif K == "secure":
                RA(str(self._reserved[K]))
            elif K == "httponly":
                RA(str(self._reserved[K]))
            else:
                RA("%s=%s" % (self._reserved[K], V))

        ##

        return _semispacejoin(result)
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


_LegalCharsPatt  = r"[\w\d!#%&'~_`><@,:/\$\*\+\-\.\^\|\)\(\?\}\{\=\[\]\_]"

_CookiePattern = re.compile(
    r"(?x)"                       ##

    r"(?P<key>"                   ##

    ""+ _LegalCharsPatt +"+?"     ##

    r")"                          ##

    r"\s*=\s*"                    ##

    r"(?P<val>"                   ##

    r'"(?:[^\\"]|\\.)*"'            ##

    r"|"                            ##

    r"\w{3},\s[\w\d-]{9,11}\s[\d:]{8}\sGMT" ##

    r"|"                            ##

    ""+ _LegalCharsPatt +"*"        ##

    r")"                          ##

    r"\s*;?"                      ##

    )


##

##

##

##

class BaseCookie(dict):
    ##

    ##


    def value_decode(self, val):
        ''''''

        return val, val
    ##


    def value_encode(self, val):
        ''''''

        strval = str(val)
        return strval, strval
    ##


    def __init__(self, input=None):
        if input: self.load(input)
    ##


    def __set(self, key, real_value, coded_value):
        ''''''

        M = self.get(key, Morsel())
        M.set(key, real_value, coded_value)
        dict.__setitem__(self, key, M)
    ##


    def __setitem__(self, key, value):
        ''''''

        rval, cval = self.value_encode(value)
        self.__set(key, rval, cval)
    ##


    def output(self, attrs=None, header="Set-Cookie:", sep="\015\012"):
        ''''''

        result = []
        items = self.items()
        items.sort()
        for K,V in items:
            result.append( V.output(attrs, header) )
        return sep.join(result)
    ##


    __str__ = output

    def __repr__(self):
        L = []
        items = self.items()
        items.sort()
        for K,V in items:
            L.append( '%s=%s' % (K,repr(V.value) ) )
        return '<%s: %s>' % (self.__class__.__name__, _spacejoin(L))

    def js_output(self, attrs=None):
        ''''''

        result = []
        items = self.items()
        items.sort()
        for K,V in items:
            result.append( V.js_output(attrs) )
        return _nulljoin(result)
    ##


    def load(self, rawdata):
        ''''''

        if type(rawdata) == type(""):
            self.__ParseString(rawdata)
        else:
            ##

            for k, v in rawdata.items():
                self[k] = v
        return
    ##


    def __ParseString(self, str, patt=_CookiePattern):
        i = 0            ##

        n = len(str)     ##

        M = None         ##


        while 0 <= i < n:
            ##

            match = patt.search(str, i)
            if not match: break          ##


            K,V = match.group("key"), match.group("val")
            i = match.end(0)

            ##

            if K[0] == "$":
                ##

                ##

                ##

                if M:
                    M[ K[1:] ] = V
            elif K.lower() in Morsel._reserved:
                if M:
                    M[ K ] = _unquote(V)
            else:
                rval, cval = self.value_decode(V)
                self.__set(K, rval, cval)
                M = self[K]
    ##

##


class SimpleCookie(BaseCookie):
    ''''''

    def value_decode(self, val):
        return _unquote( val ), val
    def value_encode(self, val):
        strval = str(val)
        return strval, _quote( strval )
##


class SerialCookie(BaseCookie):
    ''''''

    def __init__(self, input=None):
        warnings.warn("SerialCookie class is insecure; do not use it",
                      DeprecationWarning)
        BaseCookie.__init__(self, input)
    ##

    def value_decode(self, val):
        ##

        return loads( _unquote(val) ), val
    def value_encode(self, val):
        return val, _quote( dumps(val) )
##


class SmartCookie(BaseCookie):
    ''''''

    def __init__(self, input=None):
        warnings.warn("Cookie/SmartCookie class is insecure; do not use it",
                      DeprecationWarning)
        BaseCookie.__init__(self, input)
    ##

    def value_decode(self, val):
        strval = _unquote(val)
        try:
            return loads(strval), val
        except:
            return strval, val
    def value_encode(self, val):
        if type(val) == type(""):
            return val, _quote(val)
        else:
            return val, _quote( dumps(val) )
##



##

##


##

Cookie = SmartCookie

##

##


def _test():
    import doctest, Cookie
    return doctest.testmod(Cookie)

if __name__ == "__main__":
    _test()


##

##

##

