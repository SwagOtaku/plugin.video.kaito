import json
import bs4 as bs
import re
import itertools
from functools import partial
from ..ui import utils, source_utils
from ..ui.BrowserBase import BrowserBase
from ..debrid import real_debrid, all_debrid
from ..ui import database
import requests
import threading

import copy

class sources(BrowserBase):
    def get_sources(self, anilist_id, episode, get_backup):
        slugs = database.get(get_backup, 168, anilist_id, 'Animixplay')
        if not slugs:
            return []
        slugs = slugs.keys()
        mapfunc = partial(self._process_animixplay, show_id=anilist_id, episode=episode)
        all_results = map(mapfunc, slugs)
        all_results = list(itertools.chain(*all_results))
        return all_results

    def _process_animixplay(self, slug, show_id, episode):
        url = "https://animixplay.com/%s" % (requests.utils.unquote(slug))
        url = str(url)
        result = database.get(self._get_animixplay_link, 12, url)
        if not result:
            return []

        episodes = result['episodes']

        if not episodes:
            return []

        title = result['title']
        source = []

        try:
            source = [{
                'release_title': title,
                'hash': episodes[int(episode)-1],
                'type': 'embed',
                'quality': 'NA',
                'debrid_provider': '',
                'provider': 'anixplay',
                'size': 'NA',
                'info': source_utils.getInfo(title),
                'lang': source_utils.getAudio_lang(title)
                }]
        except:
            pass

        return source

    def _get_animixplay_link(self, url):
        result = requests.get(url).text
        soup = bs.BeautifulSoup(result, 'html.parser')

        if '/v2/' in url or '/v4/' in url:
            url_id = str.encode(url.split("/")[4])
            url_id = base64.b64encode(url_id).decode()
            post_id = ('NaN{}N4CP9Eb6laO9N'.format(url_id)).encode()
            post_id = base64.b64encode(post_id).decode()
            title = soup.find('span', {'class':'animetitle'}).get_text()
            data_id = 'id2' if '/v4/' in url else 'id'
            try: 
                data = (requests.post('https://animixplay.com/raw/2ENCwGVubdvzrQ2eu4hBH',
                                     data={data_id:post_id}).json())
            except:
                if '/v4/' in url:
                    data = (requests.post('https://animixplay.com/e4/5SkyXQULLrn9OhR',
                                         data={'id':url.split('/')[-1]}).json())['epstream']
                if '/v2' in url:
                    data = (requests.post('https://animixplay.com/e2/T23nBBj3NfRzTQx',
                                         data={'id':url.split('/')[-1]}).json())['epstream']

            if '/v4/' in url:
                if int(episode) > len(data):
                    return []
                # Has a list of mp4 links.
##                return data

            elif '/v2/' in url:
            # Has elaborate list for all metadata on episodes.
                data = []
                for i in data:
                    info_dict = i.get('src', None)
                    # Looks like mp4 is always first in the list
                    # Sometimes it returns None
                    if info_dict:
                        srcs = []
                        for k in info_dict:
                            if k['type'] == 'mp4':
                                srcs.append({'file': k.get('file', ''), 'flavor': k.get('lang', ''), 'res': k.get('resolution', '')})

                        data.append(srcs)
##                    else:
##                        episodes.append('')
                if int(episode) > len(data):
                    return []

            return {'title': title, 'episodes': data}

        else:
            try:
                ep_list = soup.find('div', {'id':'epslistplace'}).get_text()
                title = soup.find('span', {'class':'animetitle'}).get_text()
                jdata = json.loads(ep_list)
##                keyList = list(jdata.keys())
##                del keyList[0]

                ep_total = jdata['eptotal']
                episodes = jdata['stape']
                episodes_total = len(episodes)
                if ep_total == episodes_total:
                    return {'title': title, 'episodes': episodes}

                if ep_total > 30:
                    return {'episodes': None}

                episodes = self._get_animixplay_link_gen(url, ep_total, episodes_total)
                return {'title': title, 'episodes': episodes}
            except:
                # Link generation
                jdata = (requests.post('https://animixplay.com/e5/dZ40LAuJHZjuiWX',
                                     data={'id':url.split('/')[-1]}).json())

                title = jdata['details']['title']

                ep_total = jdata['epstream']['eptotal']
                episodes = jdata['epstream']['stape']
                episodes_total = len(episodes)
                if ep_total == episodes_total:
                    return {'title': title, 'episodes': episodes}

                if ep_total > 30:
                    return {'episodes': None}

                episodes = self._get_animixplay_link_gen(url, ep_total, episodes_total)
                return {'title': title, 'episodes': episodes}

    def _get_animixplay_link_gen(self, url, ep_total, episodes_total):
        ep_load = ep_total - episodes_total
        _range = ep_load // 12 + (ep_load % 12 > 0)
        if _range > 3:
            return {'episodes': None}
        loadmore = episodes_total
        s = requests.Session()
        for i in range(_range):
            data = (s.post('https://animixplay.com/e5/dZ40LAuJHZjuiWX',
                                  data={'id':url.split('/')[-1], 'loadmore':loadmore}))
            loadmore += 12
##            time.sleep(1)

        return data.json()['epstream']['stape']
