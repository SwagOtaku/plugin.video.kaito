import itertools
import json
import pickle
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
                slugs = [items[0].get('href').split('/')[-1]]
            else:
                slugs = [
                    item.get('href').split('/')[-1]
                    for item in items
                    if (item.find('p', {'class': 'infotext'}).text.split(',')[0].lower() + '  ').startswith(title.lower() + '  ')
                ]

        if not slugs:
            if len(items) > 1:
                slugs = [items[0].get('href').split('/')[-1]]
            else:
                return []
        slugs = list(slugs.keys()) if isinstance(slugs, dict) else slugs
        mapfunc = partial(self._process_animixplay, show_id=anilist_id, episode=episode)
        all_results = list(map(mapfunc, slugs))
        all_results = list(itertools.chain(*all_results))
        return all_results

    def _process_animixplay(self, slug, show_id, episode):
        sources = []
        headers = {'Referer': self._BASE_URL}
        url = "%sv1/%s" % (self._BASE_URL, slug)
        title = (slug.replace('-', ' ')).title() + '  Episode-{0}'.format(episode)
        r = database.get(self._send_request, 8, url, headers=headers)
        soup = BeautifulSoup(r, 'html.parser')
        eps = soup.find('div', {'id': 'epslistplace'})
        if eps:
            links = json.loads(eps.text)
            url = links.get(str(int(episode) - 1))
            if url:
                s = url.split('?id=')[-1].split('&')[0]
                url = self._BASE_URL + 'api/cW9' + self._bencode(s + 'LTXs3GrU8we9O' + self._bencode(s))
                link = self._get_redirect_url(url, headers=headers)
                if link:
                    link = link.split('#')[1]
                    link = self._bdecode(link)
                    source = {
                        'release_title': title,
                        'hash': link,
                        'type': 'direct',
                        'quality': 'EQ',
                        'debrid_provider': '',
                        'provider': 'animix',
                        'size': 'NA',
                        'info': source_utils.getInfo(slug),
                        'lang': source_utils.getAudio_lang(title)
                    }
                    sources.append(source)

        return sources
