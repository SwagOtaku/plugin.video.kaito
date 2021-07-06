import re
from six.moves import urllib_parse
from resources.lib.ui import utils, http
import requests
import json
from bs4 import BeautifulSoup

_EMBED_EXTRACTORS = {}


def register_wonderful_subs(base_url, token):
    __register_extractor(["{}/media/stream".format(base_url)],
                         __wrapper_add_token, data=(token, __extract_wonderfulsubs))


def load_video_from_url(in_url):
    found_extractor = None

    for extractor in list(_EMBED_EXTRACTORS.keys()):
        if in_url.startswith(extractor):
            found_extractor = _EMBED_EXTRACTORS[extractor]
            break

    if found_extractor is None:
        print("[*E*] No extractor found for %s" % in_url)
        return None

    try:
        if found_extractor['preloader'] is not None:
            print("Modifying Url: %s" % in_url)
            in_url = found_extractor['preloader'](in_url)

        data = found_extractor['data']
        if data is not None:
            return found_extractor['parser'](in_url,
                                             data)

        print("Probing source: %s" % in_url)
        reqObj = http.send_request(in_url)
        return found_extractor['parser'](http.raw_url(reqObj.url),
                                         reqObj.text,
                                         http.get_referer(in_url))
    except http.URLError:
        return None  # Dead link, Skip result
    except:
        raise

    return None


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
                print("[*] Skiping Invalid Url: %s - status = %d" % (item[1], temp_req.status_code))
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

    results = __check_video_list(url,
                                 map(lambda x: (x['label'],
                                                x['src'],
                                                x['captions']['src'] if 'captions' in x.keys() else None), res["urls"]))

    return results


def __extract_rapidvideo(url, page_content, referer=None):
    soup = BeautifulSoup(page_content, 'html.parser')
    # results = map(lambda x: (x['label'], x['src']),
    #               soup.select('source'))
    results = [(x['label'], x['src']) for x in soup.select('source')]
    return results


def __extract_mp4upload(url, page_content, referer=None):
    SOURCE_RE_1 = re.compile(r'.*?\|IFRAME\|(\d+)\|.*?\|\d+\|false\|h1\|w1\|(.*?)\|.*?',
                             re.DOTALL)
    SOURCE_RE_2 = re.compile(r'.*?\|video\|(.*?)\|(\d+)\|.*?',
                             re.DOTALL)
    label, domain = SOURCE_RE_1.match(page_content).groups()
    video_id, protocol = SOURCE_RE_2.match(page_content).groups()
    stream_url = 'https://{}.mp4upload.com:{}/d/{}/video.mp4'
    stream_url = stream_url.format(domain, protocol, video_id)
    stream = [(label, stream_url)]
    return stream


def __extract_streamtape(url, data):
    res = requests.get(url).text
    soup = BeautifulSoup(res, 'html.parser')
    videolink = soup.select('div#videolink')
    if not videolink:
        return
    videolink = videolink[0].text
    stream_link = 'https:' + videolink if videolink.startswith('//') else videolink
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
            print(url)
            print(content)
            print(compiled_regex.findall(content))
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
            print("[*E*] Failed to load link: %s: %s" % (url, e))
            return None
    return f


__register_extractor(["http://mp4upload.com/",
                      "http://www.mp4upload.com/",
                      "https://www.mp4upload.com/",
                      "https://mp4upload.com/"],
                     __extract_mp4upload)

__register_extractor(["https://vidstreaming.io",
                      "https://gogo-stream.com",
                      "https://gogo-play.net"],
                     __extract_vidstream,
                     None,
                     [{'d': 'https://vidstreaming.io'},
                      {'d': 'https://gogo-stream.com'},
                      {'d': 'https://gogo-play.net'}])

__register_extractor(["https://www.xstreamcdn.com/v/",
                      "https://gcloud.live/v/",
                      "https://www.fembed.com/v/",
                      "https://www.novelplanet.me/v/",
                      "https://fcdn.stream/v/"],
                     __extract_xstreamcdn,
                     lambda x: x.replace('/v/', '/api/source/'),
                     [{'d': 'www.xstreamcdn.com'},
                      {'d': 'gcloud.live'},
                      {'d': 'www.fembed.com'},
                      {'d': 'www.novelplanet.me'},
                      {'d': 'fcdn.stream'}])

__register_extractor(["https://streamtape.com/e/"],
                     __extract_streamtape,
                     None,
                     [{'d': 'https://streamtape.com'}])
