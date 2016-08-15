# urllib3/exceptions.py
##

##

##

##



##


class HTTPError(Exception):
    ''''''

    pass


class PoolError(HTTPError):
    ''''''

    def __init__(self, pool, message):
        self.pool = pool
        HTTPError.__init__(self, "%s: %s" % (pool, message))


class SSLError(HTTPError):
    ''''''

    pass


##


class MaxRetryError(PoolError):
    ''''''


    def __init__(self, pool, url):
        message = "Max retries exceeded with url: %s" % url
        PoolError.__init__(self, pool, message)

        self.url = url


class HostChangedError(PoolError):
    ''''''


    def __init__(self, pool, url, retries=3):
        message = "Tried to open a foreign host with url: %s" % url
        PoolError.__init__(self, pool, message)

        self.url = url
        self.retries = retries


class TimeoutError(PoolError):
    ''''''

    pass


class EmptyPoolError(PoolError):
    ''''''

    pass


class LocationParseError(ValueError, HTTPError):
    ''''''


    def __init__(self, location):
        message = "Failed to parse: %s" % location
        super(LocationParseError, self).__init__(self, message)

        self.location = location
