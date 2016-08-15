# urllib3/request.py
##

##

##

##


try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from .filepost import encode_multipart_formdata


__all__ = ['RequestMethods']


class RequestMethods(object):
    ''''''


    _encode_url_methods = set(['DELETE', 'GET', 'HEAD', 'OPTIONS'])

    _encode_body_methods = set(['PATCH', 'POST', 'PUT', 'TRACE'])

    def urlopen(self, method, url, body=None, headers=None,
                encode_multipart=True, multipart_boundary=None,
                **kw): ##

        raise NotImplemented("Classes extending RequestMethods must implement "
                             "their own ``urlopen`` method.")

    def request(self, method, url, fields=None, headers=None, **urlopen_kw):
        ''''''

        method = method.upper()

        if method in self._encode_url_methods:
            return self.request_encode_url(method, url, fields=fields,
                                            headers=headers,
                                            **urlopen_kw)
        else:
            return self.request_encode_body(method, url, fields=fields,
                                             headers=headers,
                                             **urlopen_kw)

    def request_encode_url(self, method, url, fields=None, **urlopen_kw):
        ''''''

        if fields:
            url += '?' + urlencode(fields)
        return self.urlopen(method, url, **urlopen_kw)

    def request_encode_body(self, method, url, fields=None, headers=None,
                            encode_multipart=True, multipart_boundary=None,
                            **urlopen_kw):
        ''''''

        if encode_multipart:
            body, content_type = encode_multipart_formdata(fields or {},
                                    boundary=multipart_boundary)
        else:
            body, content_type = (urlencode(fields or {}),
                                    'application/x-www-form-urlencoded')

        headers = headers or {}
        headers.update({'Content-Type': content_type})

        return self.urlopen(method, url, body=body, headers=headers,
                            **urlopen_kw)
