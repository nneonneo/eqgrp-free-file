# urllib3/poolmanager.py
##

##

##

##


import logging

from ._collections import RecentlyUsedContainer
from .connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from .connectionpool import get_host, connection_from_url, port_by_scheme
from .exceptions import HostChangedError
from .request import RequestMethods


__all__ = ['PoolManager', 'ProxyManager', 'proxy_from_url']


pool_classes_by_scheme = {
    'http': HTTPConnectionPool,
    'https': HTTPSConnectionPool,
}

log = logging.getLogger(__name__)


class PoolManager(RequestMethods):
    ''''''


    ##


    def __init__(self, num_pools=10, **connection_pool_kw):
        self.connection_pool_kw = connection_pool_kw
        self.pools = RecentlyUsedContainer(num_pools)

    def connection_from_host(self, host, port=80, scheme='http'):
        ''''''

        pool_key = (scheme, host, port)

        ##

        ##

        pool = self.pools.get(pool_key)
        if pool:
            return pool

        ##

        pool_cls = pool_classes_by_scheme[scheme]
        pool = pool_cls(host, port, **self.connection_pool_kw)

        self.pools[pool_key] = pool

        return pool

    def connection_from_url(self, url):
        ''''''

        scheme, host, port = get_host(url)

        port = port or port_by_scheme.get(scheme, 80)

        return self.connection_from_host(host, port=port, scheme=scheme)

    def urlopen(self, method, url, **kw):
        ''''''

        conn = self.connection_from_url(url)
        try:
            return conn.urlopen(method, url, **kw)

        except HostChangedError as e:
            kw['retries'] = e.retries ##

            return self.urlopen(method, e.url, **kw)


class ProxyManager(RequestMethods):
    ''''''


    def __init__(self, proxy_pool):
        self.proxy_pool = proxy_pool

    def _set_proxy_headers(self, headers=None):
        headers = headers or {}

        ##

        headers['Accept'] = '*/*'
        headers['Proxy-Connection'] = 'Keep-Alive'

        return headers

    def urlopen(self, method, url, **kw):
        ''''''

        kw['assert_same_host'] = False
        kw['headers'] = self._set_proxy_headers(kw.get('headers'))
        return self.proxy_pool.urlopen(method, url, **kw)


def proxy_from_url(url, **pool_kw):
    proxy_pool = connection_from_url(url, **pool_kw)
    return ProxyManager(proxy_pool)
