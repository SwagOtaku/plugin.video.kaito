import base64
import binascii
import json
import random
import re
import string
import time

import six
from bs4 import BeautifulSoup
from resources.lib.ui import client, control, jsunpack
from resources.lib.ui.pyaes import AESModeOfOperationCBC, Decrypter, Encrypter
from six.moves import urllib_error, urllib_parse

_EMBED_EXTRACTORS = {}
_EDGE_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363'


def load_video_from_url(in_url):
    found_extractor = None

    for extractor in list(_EMBED_EXTRACTORS.keys()):
        if in_url.startswith(extractor):
            found_extractor = _EMBED_EXTRACTORS[extractor]
            break

    if found_extractor is None:
        control.log("[*E*] No extractor found for %s" % in_url, 'info')
        return None

    try:
        if found_extractor['preloader'] is not None:
            control.log("Modifying Url: %s" % in_url)
            in_url = found_extractor['preloader'](in_url)

        data = found_extractor['data']
        if data is not None:
            return found_extractor['parser'](in_url,
                                             data)

        control.log("Probing source: %s" % in_url)
        reqObj = client.request(in_url, output='extended')

        return found_extractor['parser'](reqObj[5],
                                         reqObj[0],
                                         reqObj[2].get('Referer'))
    except urllib_error.URLError:
        return None  # Dead link, Skip result
    except:
        raise

    return None


def __get_packed_data(html):
    packed_data = ''
    for match in re.finditer(r'(eval\s*\(function\(p,a,c,k,e.+?\)\)[;\n<])', html, re.DOTALL | re.I):
        packed_data += jsunpack.unpack(match.group(1))

    return packed_data


def __append_headers(headers):
    return '|%s' % '&'.join(['%s=%s' % (key, urllib_parse.quote_plus(headers[key])) for key in headers])


def __check_video_list(refer_url, vidlist, add_referer=False,
                       ignore_cookie=False):
    nlist = []
    headers = {}
    if add_referer:
        headers.update({'Referer': refer_url})
    for item in vidlist:
        try:
            item_url = item[1]
            temp_req = client.request(item_url, limit=0, headers=headers, output='extended')
            if temp_req[1] != '200':
                control.log("[*] Skiping Invalid Url: %s - status = %d" % (item[1], temp_req.status_code))
                continue  # Skip Item.

            out_url = temp_req[5]
            if ignore_cookie:
                out_url = client.strip_cookie_url(out_url)

            nlist.append((item[0], out_url, item[2]))
        except Exception as e:
            # Just don't add source.
            control.log('Error when checking: {0}'.format(e))
            pass

    return nlist


def __check_video(url):
    temp_req = client.request(url, limit=0, output='extended')
    if temp_req[1] != '200':
        url = None

    return url


def __extract_rapidvideo(url, page_content, referer=None):
    soup = BeautifulSoup(page_content, 'html.parser')
    results = [(x['label'], x['src']) for x in soup.select('source')]
    return results


def __extract_mp4upload(url, page_content, referer=None):
    page_content += __get_packed_data(page_content)
    r = re.search(r'src\("([^"]+)', page_content) or re.search(r'src:\s*"([^"]+)', page_content)
    headers = {'User-Agent': _EDGE_UA,
               'Referer': url,
               'verifypeer': 'false'}
    if r:
        return r.group(1) + __append_headers(headers)
    return


def __extract_kwik(url, page_content, referer=None):
    page_content += __get_packed_data(page_content)
    r = re.search(r"const\s*source\s*=\s*'([^']+)", page_content)
    if r:
        headers = {'User-Agent': _EDGE_UA,
                   'Referer': url}
        return r.group(1) + __append_headers(headers)


def __extract_okru(url, page_content, referer=None):
    pattern = r'(?://|\.)(ok\.ru|odnoklassniki\.ru)/(?:videoembed|video|live)/(\d+)'
    host, media_id = re.findall(pattern, url)[0]
    aurl = "http://www.ok.ru/dk"
    data = {'cmd': 'videoPlayerMetadata', 'mid': media_id}
    data = urllib_parse.urlencode(data)
    html = client.request(aurl, post=data)
    json_data = json.loads(html)
    if 'error' in json_data:
        return
    strurl = json_data.get('hlsManifestUrl')
    return strurl


def __extract_mixdrop(url, page_content, referer=None):
    r = re.search(r'(?:vsr|wurl|surl)[^=]*=\s*"([^"]+)', __get_packed_data(page_content))
    if r:
        surl = r.group(1)
        if surl.startswith('//'):
            surl = 'https:' + surl
        headers = {'User-Agent': _EDGE_UA,
                   'Referer': url}
        return surl + __append_headers(headers)
    return


def __extract_dood(url, page_content, referer=None):
    def dood_decode(pdata):
        t = string.ascii_letters + string.digits
        return pdata + ''.join([random.choice(t) for _ in range(10)])

    pattern = r'(?://|\.)(dood(?:stream)?\.(?:com?|watch|to|s[ho]|cx|la|w[sf]|pm))/(?:d|e)/([0-9a-zA-Z]+)'
    match = re.search(r'''dsplayer\.hotkeys[^']+'([^']+).+?function\s*makePlay.+?return[^?]+([^"]+)''', page_content, re.DOTALL)
    if match:
        host, media_id = re.findall(pattern, url)[0]
        token = match.group(2)
        nurl = 'https://{0}{1}'.format(host, match.group(1))
        html = client.request(nurl, referer=url)
        headers = {'User-Agent': _EDGE_UA,
                   'Referer': url}
        return dood_decode(html) + token + str(int(time.time() * 1000)) + __append_headers(headers)
    return


def __extract_streamlare(url, page_content, referer=None):
    pattern = r'(?://|\.)((?:streamlare|sl(?:maxed|tube|watch))\.(?:com?|org))/(?:e|v)/([0-9A-Za-z]+)'
    host, media_id = re.findall(pattern, url)[0]
    headers = {'User-Agent': _EDGE_UA, 'Referer': url}
    api_durl = 'https://{0}/api/video/download/get'.format(host)
    api_surl = 'https://{0}/api/video/stream/get'.format(host)
    data = {'id': media_id}
    html = json.loads(client.request(api_surl, XHR=True, headers=headers, post=data, jpost=True))
    result = html.get('result', {})
    source = result.get('file') \
        or result.get('Original', {}).get('file') \
        or result.get(list(result.keys())[0], {}).get('file')
    if not source:
        html = client.request(api_durl, XHR=True, headers=headers, post=data, jpost=True)
        source = json.loads(html).get('result', {}).get('Original', {}).get('url')

    if source:
        if '?token=' in source:
            t = client.request(source, redirect=False, headers=headers, output='extended')
            if t:
                source = t[2].get('Location')
        return source + __append_headers(headers)
    return


def __extract_streamtape(url, page_content, referer=None):
    groups = re.search(
        r"document\.getElementById\(.*?\)\.innerHTML = [\"'](.*?)[\"'] \+ [\"'](.*?)[\"']",
        page_content)
    stream_link = "https:" + groups.group(1) + groups.group(2)
    return stream_link


def __extract_streamsb(url, page_content, referer=None):
    def get_embedurl(host, media_id):
        def makeid(length):
            t = string.ascii_letters + string.digits
            return ''.join([random.choice(t) for _ in range(length)])

        x = '{0}||{1}||{2}||streamsb'.format(makeid(12), media_id, makeid(12))
        c1 = binascii.hexlify(x.encode('utf8')).decode('utf8')
        x = '7Vd5jIEF2lKy||nuewwgxb1qs'
        c2 = binascii.hexlify(x.encode('utf8')).decode('utf8')
        return 'https://{0}/{1}7/{2}'.format(host, c2, c1)

    pattern = r'(?://|\.)((?:streamsb|streamsss|sb(?:lanh|ani|rapic))\.(?:net|com|pro))/e/([0-9a-zA-Z]+)'
    host, media_id = re.findall(pattern, url)[0]
    eurl = get_embedurl(host, media_id)
    headers = {'User-Agent': _EDGE_UA,
               'Referer': 'https://{0}/'.format(host),
               'watchsb': 'sbstream'}
    html = client.request(eurl, headers=headers, cookie='lang=1')
    data = json.loads(html).get("stream_data", {})
    strurl = data.get('file') or data.get('backup')
    if strurl:
        headers.pop('watchsb')
        headers.update({'Origin': 'https://{0}'.format(host)})
        return strurl + __append_headers(headers)
    return


def __extract_xstreamcdn(url, data):
    res = client.request(url, post=data)
    try:
        res = json.loads(res)['data']
    except:
        return
    if res == 'Video not found or has been removed':
        return
    stream_file = res[-1]['file']
    r = client.request(stream_file, redirect=False, output='extended')
    stream_link = (r[2]['Location']).replace('https', 'http')
    return stream_link


def __extract_goload(url, page_content, referer=None):
    def _encrypt(msg, key, iv):
        key = six.ensure_binary(key)
        encrypter = Encrypter(AESModeOfOperationCBC(key, iv))
        ciphertext = encrypter.feed(msg)
        ciphertext += encrypter.feed()
        ciphertext = base64.b64encode(ciphertext)
        return six.ensure_str(ciphertext)

    def _decrypt(msg, key, iv):
        ct = base64.b64decode(msg)
        key = six.ensure_binary(key)
        decrypter = Decrypter(AESModeOfOperationCBC(key, iv))
        decrypted = decrypter.feed(ct)
        decrypted += decrypter.feed()
        return six.ensure_str(decrypted)

    pattern = r'(?://|\.)((?:gogo-(?:play|stream)|streamani|goload|gogohd|vidstreaming|gembedhd|playgo1|anihdplay|playtaku|gotaku1)\.' \
              r'(?:io|pro|net|com|cc|online))/(?:streaming|embed(?:plus)?|ajax|load)(?:\.php)?\?id=([a-zA-Z0-9-]+)'
    r = re.search(r'crypto-js\.js.+?data-value="([^"]+)', page_content)
    if r:
        host, media_id = re.findall(pattern, url)[0]
        keys = ['37911490979715163134003223491201', '54674138327930866480207815084989']
        iv = six.ensure_binary('3134003223491201')
        params = _decrypt(r.group(1), keys[0], iv)
        eurl = 'https://{0}/encrypt-ajax.php?id={1}&alias={2}'.format(
            host, _encrypt(media_id, keys[0], iv), params)
        response = client.request(eurl, XHR=True)
        try:
            response = json.loads(response).get('data')
        except:
            return
        if response:
            result = _decrypt(response, keys[1], iv)
            result = json.loads(result)
            str_url = ''
            if len(result.get('source')) > 0:
                str_url = result.get('source')[0].get('file')
            if not str_url and len(result.get('source_bk')) > 0:
                str_url = result.get('source_bk')[0].get('file')
            if str_url:
                headers = {'User-Agent': _EDGE_UA,
                           'Referer': 'https://{0}/'.format(host),
                           'Origin': 'https://{0}'.format(host)}
                return str_url + __append_headers(headers)
    return


def __register_extractor(urls, function, url_preloader=None, datas=[]):
    if type(urls) is not list:
        urls = [urls]

    if not datas:
        datas = [None] * len(urls)

    for url, data in zip(urls, datas):
        _EMBED_EXTRACTORS[url] = {
            "preloader": url_preloader,
            "parser": function,
            "data": data
        }


def __ignore_extractor(url, content, referer=None):
    return None


def __relative_url(original_url, new_url):
    if new_url.startswith("http://") or new_url.startswith("https://"):
        return new_url

    if new_url.startswith("//"):
        return "http:%s" % new_url
    else:
        return urllib_parse.urljoin(original_url, new_url)


__register_extractor(["https://www.mp4upload.com/",
                      "https://mp4upload.com/"],
                     __extract_mp4upload)

__register_extractor(["https://kwik.cx/"],
                     __extract_kwik)

__register_extractor(["https://mixdrop.co/",
                      "https://mixdrop.to/",
                      "https://mixdrop.sx/",
                      "https://mixdrop.bz/",
                      "https://mixdrop.ch/",
                      "https://mixdrp.co/"],
                     __extract_mixdrop)

__register_extractor(["https://ok.ru/",
                      "odnoklassniki.ru"],
                     __extract_okru)

__register_extractor(["https://dood.wf/",
                      "https://dood.pm/"],
                     __extract_dood)

__register_extractor(["https://gogo-stream.com",
                      "https://gogo-play.net",
                      "https://streamani.net",
                      "https://goload.one"
                      "https://goload.io/",
                      "https://goload.pro/",
                      "https://gogohd.net/",
                      "https://gogohd.pro/",
                      "https://gembedhd.com/",
                      "https://playgo1.cc/",
                      "https://anihdplay.com/",
                      "https://playtaku.net/",
                      "https://playtaku.online/",
                      "https://gotaku1.com/"],
                     __extract_goload)

__register_extractor(["https://streamlare.com/",
                      "https://slmaxed.com/",
                      "https://sltube.org/",
                      "https://slwatch.co/"],
                     __extract_streamlare)

__register_extractor(["https://www.xstreamcdn.com/v/",
                      "https://gcloud.live/v/",
                      "https://www.fembed.com/v/",
                      "https://www.novelplanet.me/v/",
                      "https://fcdn.stream/v/",
                      "https://embedsito.com",
                      "https://fplayer.info",
                      "https://fembed-hd.com",
                      "https://fembed9hd.com"],
                     __extract_xstreamcdn,
                     lambda x: x.replace('/v/', '/api/source/'),
                     [{'d': 'www.xstreamcdn.com'},
                      {'d': 'gcloud.live'},
                      {'d': 'www.fembed.com'},
                      {'d': 'www.novelplanet.me'},
                      {'d': 'fcdn.stream'},
                      {'d': 'embedsito.com'},
                      {'d': 'fplayer.info'},
                      {'d': 'fembed-hd.com'},
                      {'d': 'fembed9hd.com'}])

__register_extractor(["https://streamtape.com/e/"],
                     __extract_streamtape)

__register_extractor(["https://sbembed.com/e/",
                      "https://sbembed1.com/e/",
                      "https://sbplay.org/e/",
                      "https://sbvideo.net/e/",
                      "https://streamsb.net/e/",
                      "https://sbplay.one/e/",
                      "https://cloudemb.com/e/",
                      "https://playersb.com/e/",
                      "https://tubesb.com/e/",
                      "https://sbplay1.com/e/",
                      "https://embedsb.com/e/",
                      "https://watchsb.com/e/",
                      "https://sbplay2.com/e/",
                      "https://japopav.tv/e/",
                      "https://viewsb.com/e/",
                      "https://sbplay2.xyz/e/",
                      "https://sbfast.com/e/",
                      "https://sbfull.com/e/",
                      "https://javplaya.com/e/",
                      "https://ssbstream.net/e/",
                      "https://p1ayerjavseen.com/e/",
                      "https://sbthe.com/e/",
                      "https://vidmovie.xyz/e/",
                      "https://sbspeed.com/e/",
                      "https://streamsss.net/e/",
                      "https://sblanh.com/e/",
                      "https://sbani.pro/e/",
                      "https://sbrapid.com/e/"],
                     __extract_streamsb)
