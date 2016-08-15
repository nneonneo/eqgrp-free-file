# -*- coding: utf-8 -*-

"""
requests.api
~~~~~~~~~~~~

This module implements the Requests API.

:copyright: (c) 2012 by Kenneth Reitz.
:license: ISC, see LICENSE for more details.

"""

from . import sessions

def request(method, url, **kwargs):
    ''''''


    s = kwargs.pop('session') if 'session' in kwargs else sessions.session()
    return s.request(method=method, url=url, **kwargs)



def get(url, **kwargs):
    ''''''


    kwargs.setdefault('allow_redirects', True)
    return request('get', url, **kwargs)


def options(url, **kwargs):
    ''''''


    kwargs.setdefault('allow_redirects', True)
    return request('options', url, **kwargs)


def head(url, **kwargs):
    ''''''


    kwargs.setdefault('allow_redirects', False)
    return request('head', url, **kwargs)


def post(url, data=None, **kwargs):
    ''''''


    return request('post', url, data=data, **kwargs)


def put(url, data=None, **kwargs):
    ''''''


    return request('put', url, data=data, **kwargs)


def patch(url, data=None, **kwargs):
    ''''''


    return request('patch', url,  data=data, **kwargs)


def delete(url, **kwargs):
    ''''''


    return request('delete', url, **kwargs)
