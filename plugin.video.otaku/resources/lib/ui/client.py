# -*- coding: utf-8 -*-

"""
    Otaku Add-on

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import re
import sys
import six
from six.moves import urllib_request, urllib_parse, urllib_error, urllib_response, http_cookiejar
import gzip
import time
import random
import json
from kodi_six import xbmc, xbmcvfs
from resources.lib.ui import control, database

TRANSLATEPATH = xbmcvfs.translatePath if six.PY3 else xbmc.translatePath
CERT_FILE = TRANSLATEPATH('special://xbmc/system/certs/cacert.pem')
_COOKIE_HEADER = "Cookie"
_HEADER_RE = re.compile(r"^([\w\d-]+?)=(.*?)$")


def request(
        url,
        close=True,
        redirect=True,
        error=False,
        verify=True,
        proxy=None,
        post=None,
        headers={},
        mobile=False,
        XHR=False,
        limit=None,
        referer='',
        cookie=None,
        compression=True,
        output='',
        timeout=20,
        jpost=False,
        params=None,
        method=''
):
    try:
        if not url:
            return
        _headers = {}
        if headers:
            _headers.update(headers)
        if _headers.get('verifypeer', '') == 'false':
            verify = False
            _headers.pop('verifypeer')

        handlers = []

        if proxy is not None:
            handlers += [urllib_request.ProxyHandler(
                {'http': '%s' % proxy}), urllib_request.HTTPHandler]
            opener = urllib_request.build_opener(*handlers)
            opener = urllib_request.install_opener(opener)

        if params is not None:
            if isinstance(params, dict):
                params = urllib_parse.urlencode(params)
            url = url + '?' + params

        if output == 'cookie' or output == 'extended' or not close:
            cookies = http_cookiejar.LWPCookieJar()
            handlers += [urllib_request.HTTPHandler(),
                         urllib_request.HTTPSHandler(),
                         urllib_request.HTTPCookieProcessor(cookies)]
            opener = urllib_request.build_opener(*handlers)
            opener = urllib_request.install_opener(opener)

        if output == 'elapsed':
            start_time = time.time() * 1000

        try:
            import platform
            node = platform.uname()[1]
        except BaseException:
            node = ''

        if verify is False and sys.version_info >= (2, 7, 12):
            try:
                import ssl
                ssl_context = ssl._create_unverified_context()
                ssl._create_default_https_context = ssl._create_unverified_context
                ssl_context.set_alpn_protocols(['http/1.1'])
                handlers += [urllib_request.HTTPSHandler(context=ssl_context)]
                opener = urllib_request.build_opener(*handlers)
                opener = urllib_request.install_opener(opener)
            except BaseException:
                pass

        if verify and ((2, 7, 8) < sys.version_info < (2, 7, 12)
                       or node == 'XboxOne'):
            try:
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                ssl_context.set_alpn_protocols(['http/1.1'])
                handlers += [urllib_request.HTTPSHandler(context=ssl_context)]
                opener = urllib_request.build_opener(*handlers)
                opener = urllib_request.install_opener(opener)
            except BaseException:
                pass
        else:
            try:
                import ssl
                ssl_context = ssl.create_default_context(cafile=CERT_FILE)
                ssl_context.set_alpn_protocols(['http/1.1'])
                handlers += [urllib_request.HTTPSHandler(context=ssl_context)]
                opener = urllib_request.build_opener(*handlers)
                opener = urllib_request.install_opener(opener)
            except BaseException:
                pass

        if url.startswith('//'):
            url = 'http:' + url

        if 'User-Agent' in _headers:
            pass
        elif mobile:
            _headers['User-Agent'] = database.get(randommobileagent, 1)
        else:
            _headers['User-Agent'] = database.get(randomagent, 1)

        if 'Referer' in _headers:
            pass
        elif referer:
            _headers['Referer'] = referer

        if 'Accept-Language' not in _headers:
            _headers['Accept-Language'] = 'en-US,en'

        if 'Accept' not in _headers:
            _headers['Accept'] = '*/*'

        if 'X-Requested-With' in _headers:
            pass
        elif XHR:
            _headers['X-Requested-With'] = 'XMLHttpRequest'

        if 'Cookie' in _headers:
            pass
        elif cookie is not None:
            if isinstance(cookie, dict):
                cookie = '; '.join(['{0}={1}'.format(x, y) for x, y in six.iteritems(cookie)])
            _headers['Cookie'] = cookie

        if 'Accept-Encoding' in _headers:
            pass
        elif compression and limit is None:
            _headers['Accept-Encoding'] = 'gzip'

        if redirect is False:
            class NoRedirectHandler(urllib_request.HTTPRedirectHandler):
                def http_error_302(self, req, fp, code, msg, headers):
                    infourl = urllib_response.addinfourl(fp, headers, req.get_full_url())
                    if sys.version_info < (3, 9, 0):
                        infourl.status = code
                        infourl.code = code
                    return infourl
                http_error_300 = http_error_302
                http_error_301 = http_error_302
                http_error_303 = http_error_302
                http_error_307 = http_error_302

            opener = urllib_request.build_opener(NoRedirectHandler())
            urllib_request.install_opener(opener)

            try:
                del _headers['Referer']
            except BaseException:
                pass

        url = byteify(url.replace(' ', '%20'))
        req = urllib_request.Request(url)

        if post is not None:
            if jpost:
                post = json.dumps(post)
                post = post.encode('utf8') if six.PY3 else post
                req = urllib_request.Request(url, post)
                req.add_header('Content-Type', 'application/json')
            else:
                if isinstance(post, dict):
                    post = byteify(post)
                    post = urllib_parse.urlencode(post)
                if len(post) > 0:
                    post = post.encode('utf8') if six.PY3 else post
                    req = urllib_request.Request(url, data=post)
                else:
                    req.get_method = lambda: 'POST'
                    req.has_header = lambda header_name: (
                        header_name == 'Content-type'
                        # or urllib_request.Request.has_header(request, header_name)
                    )

        if limit == '0':
            req.get_method = lambda: 'HEAD'

        if method:
            req.get_method = lambda: method

        _add_request_header(req, _headers)

        try:
            response = urllib_request.urlopen(req, timeout=timeout)
        except urllib_error.HTTPError as e:
            response = e
            server = response.info().getheader('Server') if six.PY2 else response.info().get('Server')
            if server and response.code == 403 and "cloudflare" in server.lower():
                import ssl
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2 if six.PY3 else ssl.PROTOCOL_TLSv1_1)
                ctx.set_alpn_protocols(['http/1.1'])
                handle = [urllib_request.HTTPSHandler(context=ctx)]
                opener = urllib_request.build_opener(*handle)
                try:
                    response = opener.open(req, timeout=30)
                except BaseException:
                    if 'return' in error:
                        # Give up
                        control.log('Request-HTTPError (%s): %s' % (response.code, url))
                        return ''
                    else:
                        if not error:
                            return ''
            elif output == '':
                control.log('Request-HTTPError (%s): %s' % (response.code, url))
                if not error:
                    return ''
        except urllib_error.URLError as e:
            response = e
            if output == '':
                control.log('Request-Error (%s): %s' % (e.reason, url))
                return ''

        if output == 'cookie':
            try:
                result = '; '.join(['%s=%s' % (i.name, i.value)
                                    for i in cookies])
            except BaseException:
                pass
            if close:
                response.close()
            return result

        elif output == 'elapsed':
            result = (time.time() * 1000) - start_time
            if close:
                response.close()
            return int(result)

        elif output == 'geturl':
            result = response.url
            if close:
                response.close()
            return result

        elif output == 'headers':
            result = response.headers
            if close:
                response.close()
            return result

        elif output == 'chunk':
            try:
                content = int(response.headers['Content-Length'])
            except BaseException:
                content = (2049 * 1024)
            if content < (2048 * 1024):
                return
            result = response.read(16 * 1024)
            if close:
                response.close()
            return result

        elif output == 'file_size':
            try:
                content = int(response.headers['Content-Length'])
            except BaseException:
                content = '0'
            response.close()
            return content

        if limit == '0':
            result = response.read(1 * 1024)
        elif limit is not None:
            result = response.read(int(limit) * 1024)
        else:
            result = response.read(5242880)

        encoding = None
        text_content = False

        if response.headers.get('content-encoding', '').lower() == 'gzip':
            result = gzip.GzipFile(fileobj=six.BytesIO(result)).read()

        content_type = response.headers.get('content-type', '').lower()

        text_content = any(x in content_type for x in ['text', 'json', 'xml', 'mpegurl'])
        if 'charset=' in content_type:
            encoding = content_type.split('charset=')[-1]

        if 'text/vtt' in content_type or url.endswith('.srt') or url.endswith('.vtt'):
            encoding = 'utf8'

        if encoding is None:
            epatterns = [r'<meta\s+http-equiv="Content-Type"\s+content="(?:.+?);\s+charset=(.+?)"',
                         r'xml\s*version.+encoding="([^"]+)']
            for epattern in epatterns:
                epattern = epattern.encode('utf8') if six.PY3 else epattern
                r = re.search(epattern, result, re.IGNORECASE)
                if r:
                    encoding = r.group(1).decode('utf8') if six.PY3 else r.group(1)
                    break

        if encoding is None:
            r = re.search(b'^#EXT', result, re.IGNORECASE)
            if r:
                encoding = 'utf8'

        if encoding is not None:
            result = result.decode(encoding, errors='ignore')
            text_content = True
        elif text_content and encoding is None:
            result = result.decode('latin-1', errors='ignore') if six.PY3 else result
        else:
            control.log('Unknown Page Encoding')

        if output == 'extended':
            try:
                response_headers = dict(
                    [(item[0].title(), item[1]) for item in list(response.info().items())])
            except BaseException:
                response_headers = response.headers
            response_url = response.url
            response_code = str(response.code)
            try:
                cookie = '; '.join(['%s=%s' % (i.name, i.value)
                                    for i in cookies])
            except BaseException:
                pass

            if close:
                response.close()
            return (result, response_code, response_headers, _headers, cookie, response_url)
        else:
            if close:
                response.close()
            return result
    except Exception as e:
        control.log('Request-Error: (%s) => %s' % (str(e), url), 'info')
        return


def _basic_request(url, headers={}, post=None, timeout=30, limit=None):
    try:
        if post is not None:
            post = post if six.PY2 else post.encode()
        request = urllib_request.Request(url, data=post)
        _add_request_header(request, headers)
        response = urllib_request.urlopen(request, timeout=timeout)
        return _get_result(response, limit)
    except BaseException:
        return


def _add_request_header(_request, headers):
    try:
        if six.PY2:
            scheme = _request.get_type()
            host = _request.get_host()
        else:
            scheme = urllib_parse.urlparse(_request.get_full_url()).scheme
            host = _request.host

        referer = headers.get('Referer', '') or '%s://%s/' % (scheme, host)

        _request.add_unredirected_header('Host', host)
        _request.add_unredirected_header('Referer', referer)
        for key in headers:
            _request.add_header(key, headers[key])
    except BaseException:
        # import traceback
        # traceback.print_exc()
        return


def _get_result(response, limit=None):
    if limit == '0':
        result = response.read(224 * 1024)
    elif limit:
        result = response.read(int(limit) * 1024)
    else:
        result = response.read(5242880)

    try:
        encoding = response.info().getheader('Content-Encoding')
    except BaseException:
        encoding = None
    if encoding == 'gzip':
        result = gzip.GzipFile(fileobj=six.BytesIO(result)).read()

    return result


def randomagent():
    _agents = [
        # 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
        'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.991',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/604.4.7 (KHTML, like Gecko) Version/11.0.2 Safari/604.4.7',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:54.0) Gecko/20100101 Firefox/54.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0']
    return random.choice(_agents)


def randommobileagent():
    _mobagents = [
        'Mozilla/5.0 (Linux; Android 7.1; vivo 1716 Build/N2G47H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.98 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; U; Android 6.0.1; zh-CN; F5121 Build/34.0.A.1.247) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/40.0.2214.89 UCBrowser/11.5.1.944 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 7.0; SAMSUNG SM-N920C Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/6.2 Chrome/56.0.2924.87 Mobile Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 11_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 10_2_1 like Mac OS X) AppleWebKit/602.4.6 (KHTML, like Gecko) Version/10.0 Mobile/14D27 Safari/602.1']
    return random.choice(_mobagents)


def agent():
    return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'


def byteify(data, ignore_dicts=False):
    if isinstance(data, six.text_type) and six.PY2:
        return data.encode('utf-8')
    if isinstance(data, list):
        return [byteify(item, ignore_dicts=True) for item in data]
    if isinstance(data, dict) and not ignore_dicts:
        return dict([(byteify(key, ignore_dicts=True), byteify(
            value, ignore_dicts=True)) for key, value in six.iteritems(data)])
    return data


def strip_cookie_url(url):
    url, headers = _strip_url(url)
    if _COOKIE_HEADER in headers.keys():
        del headers[_COOKIE_HEADER]

    return _url_with_headers(url, headers)


def _url_with_headers(url, headers):
    if not len(headers.keys()):
        return url

    headers_arr = ["%s=%s" % (key, urllib_parse.quote_plus(value)) for key, value in
                   six.iteritems(headers)]

    return "|".join([url] + headers_arr)


def _strip_url(url):
    if url.find('|') == -1:
        return (url, {})

    headers = url.split('|')
    target_url = headers.pop(0)
    out_headers = {}
    for h in headers:
        m = _HEADER_RE.findall(h)
        if not len(m):
            continue

        out_headers[m[0][0]] = urllib_parse.unquote_plus(m[0][1])

    return (target_url, out_headers)
