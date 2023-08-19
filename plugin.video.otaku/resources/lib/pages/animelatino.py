import json
import pickle
import re

from resources.lib.ui import database, source_utils
from resources.lib.ui.BrowserBase import BrowserBase


class sources(BrowserBase):
    _BASE_URL = 'https://www.animelatinohd.com/'
    _API_URL = 'https://api.animelatinohd.com/'
    BID = 'w51kDCy70VSuxmn7Usaie'

    def get_sources(self, anilist_id, episode, get_backup):
        show = database.get_show(anilist_id)
        kodi_meta = pickle.loads(show.get('kodi_meta'))
        title = kodi_meta.get('name')
        title = self._clean_title(title)
        headers = {'Referer': self._BASE_URL}

        res = database.get(
            self._get_request,
            168,
            self._BASE_URL,
            headers=headers
        )
        r = re.search(r'"buildId":"([^"]+)', res)
        if r:
            self.BID = r.group(1)

        headers.update({'Origin': self._BASE_URL[:-1]})
        params = {'search': title}
        res = database.get(
            self._get_request,
            8,
            self._API_URL + 'api/anime/search',
            data=params,
            headers=headers
        )
        items = json.loads(res)

        if not items and ':' in title:
            title = title.split(':')[0]
            params = {'search': title}
            res = database.get(
                self._get_request,
                8,
                self._BASE_URL,
                data=params,
                headers=headers
            )
            items = json.loads(res)

        all_results = []
        if items:
            if title[-1].isdigit():
                items = [x for x in items if title.lower() in x.get('name').lower()]
            else:
                items = [x for x in items if (title.lower() + '  ') in (x.get('name').lower() + '  ')]
            if items:
                slug = items[0].get('slug')
                all_results = self._process_al(slug, title=title, episode=episode)

        return all_results

    def _process_al(self, slug, title, episode):
        sources = []
        headers = {'Referer': self._BASE_URL, 'x-nextjs-data': 1}
        url = '{0}_next/data/{1}/anime/{2}.json'.format(
            self._BASE_URL,
            self.BID,
            slug
        )
        params = {'slug': slug}
        res = database.get(
            self._get_request,
            8,
            url,
            data=params,
            headers=headers
        )

        items = json.loads(res).get('pageProps', {}).get('data', {}).get('episodes')
        e_id = [x.get('number') for x in items if x.get('number') == int(episode)]
        if e_id:
            url = '{0}_next/data/{1}/ver/{2}/{3}.json'.format(
                self._BASE_URL,
                self.BID,
                slug,
                e_id[0]
            )
            params.update({'number': e_id[0]})
            res = self._get_request(url, data=params, headers=headers)
            headers.pop('x-nextjs-data')
            items = json.loads(res).get('pageProps', {}).get('data', {}).get('players')
            for item in items:
                for src in item:
                    lang = 'SUB' if src.get('languaje') == '0' else 'DUB'
                    sid = src.get('id')
                    surl = '{0}stream/{1}'.format(self._API_URL, sid)
                    slink = self._get_redirect_url(surl, headers=headers)
                    if slink:
                        source = {
                            'release_title': '{0} - Ep {1}'.format(title, episode),
                            'hash': slink,
                            'type': 'embed',
                            'quality': 'EQ',
                            'debrid_provider': '',
                            'provider': 'animelatino',
                            'size': 'NA',
                            'info': [lang, source_utils.get_embedhost(slink)],
                            'lang': 2 if lang == 'DUB' else 0
                        }
                        sources.append(source)

        return sources
