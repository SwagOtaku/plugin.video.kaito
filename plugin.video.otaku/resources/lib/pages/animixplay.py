import itertools
import json
import pickle
import re
from functools import partial

from bs4 import BeautifulSoup
from resources.lib.ui import database, source_utils
from resources.lib.ui.BrowserBase import BrowserBase


class sources(BrowserBase):
    _BASE_URL = 'https://animixplay.to/'

    def get_sources(self, anilist_id, episode, get_backup):
        show = database.get_show(anilist_id)
        kodi_meta = pickle.loads(show.get('kodi_meta'))
        title = kodi_meta.get('ename') or kodi_meta.get('name')
        title = self._clean_title(title)

        data = {'qfast': title, 'root': 'animixplay.to'}
        headers = {'Origin': self._BASE_URL[:-1],
                   'Referer': self._BASE_URL}
        r = database.get(
            self._post_request,
            8,
            'https://cdn.animixplay.to/api/search',
            data=data,
            headers=headers
        )
        r = json.loads(r).get('result')

        soup = BeautifulSoup(r, 'html.parser')
        items = soup.find_all('a')
        slugs = []
        if items:
            if len(items) == 1:
                slugs = [items[0].get('href')]
            else:
                slugs = [
                    item.get('href')
                    for item in items
                    if (item.find('p', {'class': 'infotext'}).text.split(',')[0].lower() + '  ').startswith(title.lower() + '  ')
                ]

        if not slugs:
            if len(items) > 1:
                slugs = [items[0].get('href')]
            else:
                return []
        slugs = list(slugs.keys()) if isinstance(slugs, dict) else slugs
        url = self._BASE_URL[:-1] + slugs[0]
        s = database.get(self._send_request, 8, url, headers=headers)
        mid = re.findall(r"var\s*malid\s*=\s*'(\d+)", s)[0]
        data = {'recomended': mid}
        headers.update({'X-Requested-With': 'XMLHttpRequest'})
        t = database.get(
            self._post_request,
            8,
            self._BASE_URL + 'api/search',
            data=data,
            headers=headers
        )
        t = json.loads(t).get('data')
        links = []
        for e in t:
            for item in e.get('items'):
                links.append((item.get('url'), item.get('title')))
        mapfunc = partial(self._process_animixplay, show_id=anilist_id, episode=episode)
        all_results = list(map(mapfunc, links))
        all_results = list(itertools.chain(*all_results))
        return all_results

    def _process_animixplay(self, slug, show_id, episode):
        sources = []
        headers = {'Referer': self._BASE_URL}
        url = self._BASE_URL[:-1] + slug[0]
        title = slug[1] + ' Episode {0}'.format(episode)
        r = database.get(self._send_request, 8, url, headers=headers)
        soup = BeautifulSoup(r, 'html.parser')
        eps = soup.find('div', {'id': 'epslistplace'})
        if eps:
            try:
                links = json.loads(eps.text)
                urls = links.get(str(int(episode) - 1))
                if urls:
                    if not isinstance(urls, list):
                        urls = [urls]
                    for url in urls:
                        type_ = None
                        if isinstance(url, dict):
                            url = url.get('vid')
                        if 'gogohd.net' in url:
                            s = url.split('?id=')[-1].split('&')[0]
                            url = self._BASE_URL + 'api/cW9' + self._bencode(s + 'LTXs3GrU8we9O' + self._bencode(s))
                            link = self._get_redirect_url(url, headers=headers)
                            link = link.split('#')[1]
                            link = self._bdecode(link)
                            type_ = 'direct'
                            server = ''
                        else:
                            link = url
                            if 'ok.ru' in url:
                                server = 'ok'
                                type_ = 'embed'
                            elif 'mp4upload.com' in url:
                                server = 'mp4upload'
                                type_ = 'embed'
                            elif 'mixdrop.co' in url:
                                server = 'mixdrop'
                                type_ = 'embed'
                            elif 'streamlare.com' in url:
                                server = 'streamlare'
                                type_ = 'embed'
                            # elif 'streamsb.' in url:
                            #     server = 'streamsb'
                            #     type_ = 'embed'

                        if type_ is None:
                            continue

                        source = {
                            'release_title': title,
                            'hash': link,
                            'type': type_,
                            'quality': 'EQ',
                            'debrid_provider': '',
                            'provider': 'animix',
                            'size': 'NA',
                            'info': source_utils.getInfo(slug[0]) + [server],
                            'lang': source_utils.getAudio_lang(title)
                        }
                        sources.append(source)
            except:
                pass

        return sources
