import json
import pickle

from bs4 import BeautifulSoup, SoupStrainer
from resources.lib.ui import database, source_utils
from resources.lib.ui.BrowserBase import BrowserBase


class sources(BrowserBase):
    _BASE_URL = 'https://animepahe.ru/'

    def get_sources(self, anilist_id, episode, get_backup):
        show = database.get_show(anilist_id)
        kodi_meta = pickle.loads(show.get('kodi_meta'))
        title = kodi_meta.get('name')
        title = self._clean_title(title)
        headers = {'Referer': self._BASE_URL}
        params = {'m': 'search',
                  'q': title}
        r = database.get(
            self._get_request,
            8,
            self._BASE_URL + 'api',
            data=params,
            headers=headers,
            XHR=True
        )
        items = json.loads(r).get('data')

        if not items and ':' in title:
            title = title.split(':')[0]
            params.update({'q': title})
            r = database.get(
                self._get_request,
                8,
                self._BASE_URL + 'api',
                data=params,
                headers=headers,
                XHR=True
            )
            items = json.loads(r).get('data')

        all_results = []
        if items:
            items = [x for x in items if (x.get('title').lower() + '  ') in (title.lower() + '  ')]
            if items:
                slug = items[0].get('session')
                all_results = self._process_ap(slug, title=title, episode=episode)
        return all_results

    def _process_ap(self, slug, title, episode):
        sources = []
        params = {
            'm': 'release',
            'id': slug,
            'sort': 'episode_asc',
            'page': 1
        }
        headers = {'Referer': self._BASE_URL}
        r = database.get(
            self._get_request,
            8,
            self._BASE_URL + 'api',
            data=params,
            headers=headers,
            XHR=True
        )
        items = json.loads(r).get('data')
        e_num = int(episode)
        if items[0].get('episode') > 1:
            e_num = e_num + items[0].get('episode') - 1

        items = [x for x in items if x.get('episode') == e_num]
        if items:
            eurl = self._BASE_URL + 'play/' + slug + '/' + items[0].get('session')
            html = self._get_request(eurl, headers=headers)
            mlink = SoupStrainer('div', {'id': 'resolutionMenu'})
            mdiv = BeautifulSoup(html, "html.parser", parse_only=mlink)
            items = mdiv.find_all('button')

            for item in items:
                qual = int(item.get('data-resolution'))
                if qual < 577:
                    quality = 'NA'
                elif qual < 721:
                    quality = '720p'
                elif qual < 1081:
                    quality = '1080p'
                else:
                    quality = '4K'
                source = {
                    'release_title': '{0} - Ep {1}'.format(title, episode),
                    'hash': item.get('data-src'),
                    'type': 'embed',
                    'quality': quality,
                    'debrid_provider': '',
                    'provider': 'animepahe',
                    'size': 'NA',
                    'info': [source_utils.get_embedhost(item.get('data-src'))],
                    'lang': 2 if item.get('data-audio') == 'eng' else 0
                }
                sources.append(source)

        return sources
