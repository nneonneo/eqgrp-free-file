# -*- coding: utf-8 -*-

"""
oreos.structures
~~~~~~~~~~~~~~~~

The plastic blue packaging.

This is mostly directly stolen from mitsuhiko/werkzeug.
"""

__all__ = ('MultiDict',)

class _Missing(object):

    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'

_missing = _Missing()



def iter_multi_items(mapping):
    ''''''

    if isinstance(mapping, MultiDict):
        for item in mapping.iteritems(multi=True):
            yield item
    elif isinstance(mapping, dict):
        for key, value in mapping.iteritems():
            if isinstance(value, (tuple, list)):
                for value in value:
                    yield key, value
            else:
                yield key, value
    else:
        for item in mapping:
            yield item



class TypeConversionDict(dict):
    ''''''


    def get(self, key, default=None, type=None):
        ''''''

        try:
            rv = self[key]
            if type is not None:
                rv = type(rv)
        except (KeyError, ValueError):
            rv = default
        return rv


class MultiDict(TypeConversionDict):
    ''''''


    def __init__(self, mapping=None):
        if isinstance(mapping, MultiDict):
            dict.__init__(self, ((k, l[:]) for k, l in mapping.iterlists()))
        elif isinstance(mapping, dict):
            tmp = {}
            for key, value in mapping.iteritems():
                if isinstance(value, (tuple, list)):
                    value = list(value)
                else:
                    value = [value]
                tmp[key] = value
            dict.__init__(self, tmp)
        else:
            tmp = {}
            for key, value in mapping or ():
                tmp.setdefault(key, []).append(value)
            dict.__init__(self, tmp)

    def __getstate__(self):
        return dict(self.lists())

    def __setstate__(self, value):
        dict.clear(self)
        dict.update(self, value)

    def __iter__(self):
        return self.iterkeys()

    def __getitem__(self, key):
        ''''''

        if key in self:
            return dict.__getitem__(self, key)[0]
        raise KeyError(key)

    def __setitem__(self, key, value):
        ''''''

        dict.__setitem__(self, key, [value])

    def add(self, key, value):
        ''''''

        dict.setdefault(self, key, []).append(value)

    def getlist(self, key, type=None):
        ''''''

        try:
            rv = dict.__getitem__(self, key)
        except KeyError:
            return []
        if type is None:
            return list(rv)
        result = []
        for item in rv:
            try:
                result.append(type(item))
            except ValueError:
                pass
        return result

    def setlist(self, key, new_list):
        ''''''

        dict.__setitem__(self, key, list(new_list))

    def setdefault(self, key, default=None):
        ''''''

        if key not in self:
            self[key] = default
        else:
            default = self[key]
        return default

    def setlistdefault(self, key, default_list=None):
        ''''''

        if key not in self:
            default_list = list(default_list or ())
            dict.__setitem__(self, key, default_list)
        else:
            default_list = dict.__getitem__(self, key)
        return default_list

    def items(self, multi=False):
        ''''''

        return list(self.iteritems(multi))

    def lists(self):
        ''''''

        return list(self.iterlists())

    def values(self):
        ''''''

        return [self[key] for key in self.iterkeys()]

    def listvalues(self):
        ''''''

        return list(self.iterlistvalues())

    def iteritems(self, multi=False):
        ''''''

        for key, values in dict.iteritems(self):
            if multi:
                for value in values:
                    yield key, value
            else:
                yield key, values[0]

    def iterlists(self):
        ''''''

        for key, values in dict.iteritems(self):
            yield key, list(values)

    def itervalues(self):
        ''''''

        for values in dict.itervalues(self):
            yield values[0]

    def iterlistvalues(self):
        ''''''

        return dict.itervalues(self)

    def copy(self):
        ''''''

        return self.__class__(self)

    def to_dict(self, flat=True):
        ''''''

        if flat:
            return dict(self.iteritems())
        return dict(self.lists())

    def update(self, other_dict):
        ''''''

        for key, value in iter_multi_items(other_dict):
            MultiDict.add(self, key, value)

    def pop(self, key, default=_missing):
        ''''''

        try:
            return dict.pop(self, key)[0]
        except KeyError as e:
            if default is not _missing:
                return default
            raise KeyError(str(e))

    def popitem(self):
        ''''''

        try:
            item = dict.popitem(self)
            return (item[0], item[1][0])
        except KeyError as e:
            raise KeyError(str(e))

    def poplist(self, key):
        ''''''

        return dict.pop(self, key, [])

    def popitemlist(self):
        ''''''

        try:
            return dict.popitem(self)
        except KeyError as e:
            raise KeyError(str(e))

    def __copy__(self):
        return self.copy()

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.items(multi=True))
