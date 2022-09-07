import re
import six
from six.moves import urllib_parse
from resources.lib.ui import utils, http, control
import requests
import json
import base64
from bs4 import BeautifulSoup
from resources.lib.pyaes import AESModeOfOperationCBC, Encrypter, Decrypter
from resources.lib import jsunpack
import random
import string
import time

_EMBED_EXTRACTORS = {}


def register_wonderful_subs(base_url, token):
    __register_extractor(
        ["{}/media/stream".format(base_url)],
        __wrapper_add_token,
        data=(token, __extract_wonderfulsubs)
    )


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
            control.log("Modifying Url: %s" % in_url, 'info')
            in_url = found_extractor['preloader'](in_url)

        data = found_extractor['data']
        if data is not None:
            return found_extractor['parser'](in_url,
                                             data)

        control.log("Probing source: %s" % in_url, 'info')
        reqObj = http.send_request(in_url)
        return found_extractor['parser'](http.raw_url(reqObj.url),
                                         reqObj.text,
                                         http.get_referer(in_url))
    except http.URLError:
        return None  # Dead link, Skip result
    except:
        raise

    return None


def __get_packed_data(html):
    packed_data = ''
    for match in re.finditer(r'(eval\s*\(function.*?)</script>', html, re.DOTALL | re.I):
        if jsunpack.detect(match.group(1)):
            packed_data += jsunpack.unpack(match.group(1))

    return packed_data


def __check_video_list(refer_url, vidlist, add_referer=False,
                       ignore_cookie=False):
    nlist = []
    for item in vidlist:
        try:
            item_url = item[1]
            if add_referer:
                item_url = http.add_referer_url(item_url, refer_url)

            temp_req = http.head_request(item_url)
            if temp_req.status_code != 200:
                control.log("[*] Skiping Invalid Url: %s - status = %d" % (item[1], temp_req.status_code), 'info')
                continue  # Skip Item.

            out_url = temp_req.url
            if ignore_cookie:
                out_url = http.strip_cookie_url(out_url)

            nlist.append((item[0], out_url, item[2]))
        except Exception as e:
            # Just don't add source.
            pass

    return nlist


def __check_video(url):
    temp_req = requests.head(url)
    if not temp_req.ok:
        url = None

    return url


def __wrapper_add_token(url, data):
    token, cb = data

    def inject_token(req):
        req.add_header("Authorization", "Bearer {}".format(token))
        return req

    response = http.send_request(url, set_request=inject_token)
    return cb(url, response.text)


def __extract_wonderfulsubs(url, content, referer=None):
    res = json.loads(content)
    if res["status"] != 200:
        raise Exception("Failed with error code of %d" % res["status"])

    if "embed" in res.keys():
        embed_url = res["embed"]
        return load_video_from_url(embed_url)

    results = __check_video_list(
        url,
        map(lambda x: (x['label'],
                       x['src'],
                       x['captions']['src'] if 'captions' in x.keys() else None),
            res["urls"])
    )

    return results


def __extract_rapidvideo(url, page_content, referer=None):
    soup = BeautifulSoup(page_content, 'html.parser')
    results = [(x['label'], x['src']) for x in soup.select('source')]
    return results


def __extract_mp4upload(url, data):
    res = requests.get(url).text
    res += __get_packed_data(res)
    r = re.search(r'src\("([^"]+)', res)
    if r:
        return r.group(1) + '|Referer=https://www.mp4upload.com/&verifypeer=false'
    return


def __extract_dood(url, data):
    def dood_decode(pdata):
        t = string.ascii_letters + string.digits
        return pdata + ''.join([random.choice(t) for _ in range(10)])

    pattern = r'(?://|\.)(dood(?:stream)?\.(?:com?|watch|to|s[ho]|cx|la|w[sf]|pm))/(?:d|e)/([0-9a-zA-Z]+)'
    headers = {'User-Agent': 'Mozilla/5.0'}
    html = requests.get(url, headers=headers).text
    match = re.search(r'''dsplayer\.hotkeys[^']+'([^']+).+?function\s*makePlay.+?return[^?]+([^"]+)''', html, re.DOTALL)
    if match:
        host, media_id = re.findall(pattern, url)[0]
        token = match.group(2)
        nurl = 'https://{0}{1}'.format(host, match.group(1))
        headers.update({'Referer': url})
        html = requests.get(nurl, headers=headers).text
        return dood_decode(html) + token + str(int(time.time() * 1000))
    return


def __extract_streamtape(url, data):
    res = requests.get(url).text
    groups = re.search(
        r"document\.getElementById\(.*?\)\.innerHTML = [\"'](.*?)[\"'] \+ [\"'](.*?)[\"']",
        res)
    stream_link = "https:" + groups.group(1) + groups.group(2)
    return stream_link


def __extract_vidstream(url, data):
    res = requests.get(url).text
    SOURCE_RE = re.compile(r"file:\s'(.*?)',")
    res = SOURCE_RE.findall(res)
    stream_link = None
    if res:
        stream_link = res[0]
        if 'm3u8' in stream_link:
            stream_link = stream_link.replace('https', 'http')

        stream_link = __check_video(stream_link)

    return stream_link


def __extract_xstreamcdn(url, data):
    res = requests.post(url, data=data)
    if not res.ok:
        return
    res = res.json()['data']
    if res == 'Video not found or has been removed':
        return
    stream_file = res[-1]['file']
    r = requests.get(stream_file, allow_redirects=False)
    stream_link = (r.headers['Location']).replace('https', 'http')
    return stream_link


def __extract_goload(url, data):
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

    pattern = r'(?://|\.)((?:goload|gogohd)\.(?:io|pro|net))/(?:streaming\.php|embedplus)\?id=([a-zA-Z0-9-]+)'
    headers = {'User-Agent': 'Mozilla/5.0'}
    page_content = requests.get(url, headers=headers).text
    r = re.search(r'crypto-js\.js.+?data-value="([^"]+)', page_content)
    if r:
        host, media_id = re.findall(pattern, url)[0]
        keys = ['37911490979715163134003223491201', '54674138327930866480207815084989']
        iv = six.ensure_binary('3134003223491201')
        params = _decrypt(r.group(1), keys[0], iv)
        eurl = 'https://{0}/encrypt-ajax.php?id={1}&alias={2}'.format(
            host, _encrypt(media_id, keys[0], iv), params)
        headers.update({'X-Requested-With': 'XMLHttpRequest'})
        response = requests.get(eurl, headers=headers).json()
        response = response.get('data')
        if response:
            result = _decrypt(response, keys[1], iv)
            result = json.loads(result)
            str_url = ''
            if len(result.get('source')) > 0:
                str_url = result.get('source')[0].get('file')
            if not str_url and len(result.get('source_bk')) > 0:
                str_url = result.get('source_bk')[0].get('file')
            if str_url:
                return str_url
    return


def __register_extractor(urls, function, url_preloader=None, datas=[]):
    if type(urls) is not list:
        urls = [urls]

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


def __extractor_factory(regex, double_ref=False, match=0, debug=False):
    compiled_regex = re.compile(regex, re.DOTALL)

    def f(url, content, referer=None):
        if debug:
            control.log(url, 'info')
            control.log(content, 'info')
            control.log(compiled_regex.findall(content), 'info')
            raise

        try:
            regex_url = compiled_regex.findall(content)[match]
            regex_url = __relative_url(url, regex_url)
            if double_ref:
                video_url = utils.head_request(http.add_referer_url(regex_url, url)).url
            else:
                video_url = __relative_url(regex_url, regex_url)
            return video_url
        except Exception as e:
            control.log("[*E*] Failed to load link: %s: %s" % (url, e), 'info')
            return None
    return f


__register_extractor(["https://www.mp4upload.com/",
                      "https://mp4upload.com/"],
                     __extract_mp4upload,
                     None,
                     [{'d': 'www.mp4upload.com'},
                      {'d': 'mp4upload.com'}])

__register_extractor(["https://dood.wf/",
                      "https://dood.pm/"],
                     __extract_dood,
                     None,
                     [{'d': 'dood.wf'},
                      {'d': 'dood.pm'}])

__register_extractor(["https://goload.io/",
                      "https://goload.pro/",
                      "https://gogohd.net/"],
                     __extract_goload,
                     None,
                     [{'d': 'goload.io'},
                      {'d': 'goload.pro'},
                      {'d': 'gogohd.net'}])

__register_extractor(["https://vidstreaming.io",
                      "https://gogo-stream.com",
                      "https://gogo-play.net",
                      "https://streamani.net",
                      "https://goload.one"],
                     __extract_vidstream,
                     None,
                     [{'d': 'https://vidstreaming.io'},
                      {'d': 'https://gogo-stream.com'},
                      {'d': 'https://gogo-play.net'},
                      {'d': 'https://streamani.net'},
                      {'d': 'https://goload.one'}])

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
                     __extract_streamtape,
                     None,
                     [{'d': 'https://streamtape.com'}])
