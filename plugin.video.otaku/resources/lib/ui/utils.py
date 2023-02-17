import os
import random
import re
from resources.lib.ui import control, client
from six import StringIO
from kodi_six import xbmcvfs


def allocate_item(name, url, is_dir=False, image='', info='', fanart=None, poster=None, cast=[], landscape=None, banner=None, clearart=None, clearlogo=None):
    new_res = {}
    new_res['is_dir'] = is_dir
    if image and '/' not in image:
        image = os.path.join(control.artPath(), image)
    if fanart:
        if isinstance(fanart, list):
            fanart = random.choice(fanart)
        if '/' not in fanart:
            fanart = os.path.join(control.artPath(), fanart)
    if poster and '/' not in poster:
        poster = os.path.join(control.artPath(), poster)
    new_res['image'] = {
        'poster': poster or image,
        'icon': image,
        'thumb': image,
        'fanart': fanart,
        'landscape': landscape,
        'banner': banner,
        'clearart': clearart,
        'clearlogo': clearlogo
    }
    new_res['name'] = name
    new_res['url'] = url
    new_res['info'] = info
    new_res['cast'] = cast
    return new_res


def get_sub(sub_url, sub_lang):
    content = client.request(sub_url)
    if sub_url.endswith('.vtt'):
        replacement = re.sub(r'([\d]+)\.([\d]+)', r'\1,\2', content)
        replacement = re.sub(r'WEBVTT\n\n', '', replacement)
        replacement = re.sub(r'^\d+\n', '', replacement)
        replacement = re.sub(r'\n\d+\n', '\n', replacement)
        replacement = StringIO(replacement)
        idx = 1
        content = ''
        for line in replacement:
            if '-->' in line:
                if len(line.split(' --> ')[0]) < 12:
                    line = re.sub(
                        r'([\d]+):([\d]+),([\d]+)', r'00:\1:\2,\3', line)
                content += '%s\n%s' % (idx, line)
                idx += 1
            else:
                content += line

    subtitle = control.TRANSLATEPATH('special://temp/')
    subtitle = os.path.join(subtitle, 'TemporarySubs.{0}.srt'.format(sub_lang))
    if control.PY3:
        with open(subtitle, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        with open(subtitle, 'w') as f:
            f.write(content.encode('utf8'))

    return subtitle


def del_subs():
    dirs, files = xbmcvfs.listdir('special://temp/')
    for fname in files:
        if fname.startswith('TemporarySubs'):
            xbmcvfs.delete('special://temp/' + fname)
    return
