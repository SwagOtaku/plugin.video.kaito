# -*- coding: utf-8 -*-
import base64

import six
from resources.lib.ui import client
from six.moves import urllib_parse


class BrowserBase(object):
    _BASE_URL = None

    def _clean_title(self, text):
        return text.replace(u'×'.encode('utf-8') if six.PY2 else u'×', ' x ')

    def _to_url(self, url=''):
        assert self._BASE_URL is not None, "Must be set on inherentance"

        if url.startswith("/"):
            url = url[1:]
        return "%s/%s" % (self._BASE_URL, url)

    def _send_request(self, url, data=None, headers=None):
        return client.request(url, post=data, headers=headers)

    def _post_request(self, url, data={}, headers=None):
        return self._send_request(url, data, headers)

    def _get_request(self, url, data=None, headers=None):
        if data:
            url = "%s?%s" % (url, urllib_parse.urlencode(data))
        return self._send_request(url, None, headers)

    def _get_redirect_url(self, url, headers=None):
        t = client.request(url, redirect=False, headers=headers, output='extended')
        if t:
            return t[2].get('Location')
        return ''

    def _bencode(self, text):
        return six.ensure_str(base64.b64encode(six.ensure_binary(text)))

    def _bdecode(self, text):
        return six.ensure_str(base64.b64decode(text))
