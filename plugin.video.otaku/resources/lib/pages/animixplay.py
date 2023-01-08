import itertools
import json
import pickle
import re
from functools import partial

from bs4 import BeautifulSoup
from resources.lib.ui import database
from resources.lib.ui.BrowserBase import BrowserBase


class sources(BrowserBase):
    _BASE_URL = 'https://animixplay.as/'

    def get_sources(self, anilist_id, episode, get_backup):
        show = database.get_show(anilist_id)
        kodi_meta = pickle.loads(show.get('kodi_meta'))
        title = kodi_meta.get('ename') or kodi_meta.get('name')
        title = self._clean_title(title)

        headers = {'Origin': self._BASE_URL[:-1],
                   'Referer': self._BASE_URL}
        r = database.get(
            self._get_request,
            8,
            self._BASE_URL + 'wp-json/kiranime/v1/anime/search',
            data={'query': title},
            headers=headers
        )
        r = json.loads(r).get('result')

        if len(r) == 0:
            if ' Cour ' in title:
                title = title.replace(' Cour ', ' Part ')
            elif ' Part ' in title:
                title = title.replace(' Part ', ' Cour ')
            else:
                return []
            r = database.get(
                self._get_request,
                8,
                self._BASE_URL + 'wp-json/kiranime/v1/anime/search',
                data={'query': title},
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
                    if (item.find('h3').text.split(',')[0].lower() + '  ').startswith(title.lower() + '  ')
                ]

        if not slugs:
            if len(items) > 1:
                slugs = [items[0].get('href')]
            else:
                return []
        slugs = list(slugs.keys()) if isinstance(slugs, dict) else slugs
        mapfunc = partial(self._process_animixplay, show_id=anilist_id, episode=episode)
        all_results = list(map(mapfunc, slugs))
        all_results = list(itertools.chain(*all_results))
        return all_results

    def _process_animixplay(self, slug, show_id, episode):
        sources = []
        links = []
        headers = {'Referer': self._BASE_URL}
        url = slug.replace('/anime/', '/watch/')
        r = database.get(self._get_request, 8, url, headers=headers)
        mdata = re.search(r"var\s*anime\s*=\s*(.+?});", r)
        if mdata:
            mdata = json.loads(mdata.group(1))
            eps = mdata.get('episodes').get('lists')
            title = mdata.get('title')
            for ep in eps:
                if ep.get('number') == int(episode):
                    links = ep.get('links')
                    break
            if links:
                for link in links:
                    type_ = None
                    lang = 0 if link.get('type') == 'sub' else 2
                    server = link.get('server')
                    url = link.get('link')
                    if any(x in url for x in ['/crunchyroll/', '/gogoanime/', '/allanime/']):
                        slink = self._get_redirect_url(url, headers=headers)
                        host, slink = slink.split('#')
                        slink = self._bdecode(slink) + '|Origin={0}&Referer={0}/&User-Agent=iPad'.format(self._get_origin(host))
                        type_ = 'direct'
                    else:
                        s = database.get(self._get_request, 8, url, headers=headers)
                        slink = re.search(r"hls.loadSource\('([^']+)", s)
                        if slink:
                            slink = slink.group(1) + '|Origin={0}&Referer={0}/&User-Agent=iPad'.format(self._get_origin(url))
                            type_ = 'direct'

                    if type_ is None:
                        continue

                    source = {
                        'release_title': '{0} Ep{1}'.format(title, episode),
                        'hash': slink,
                        'type': type_,
                        'quality': 'EQ',
                        'debrid_provider': '',
                        'provider': 'animix',
                        'size': 'NA',
                        'info': [server, link.get('type')],
                        'lang': lang
                    }
                    sources.append(source)

        return sources
