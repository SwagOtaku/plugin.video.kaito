import itertools
import json
import pickle
import re
from functools import partial

from bs4 import BeautifulSoup
from resources.lib.ui import database, source_utils, utils
from resources.lib.ui.BrowserBase import BrowserBase


class sources(BrowserBase):
    _BASE_URL = 'https://gogoanime3.net/'

    def get_sources(self, anilist_id, episode, get_backup):
        show = database.get_show(anilist_id)
        kodi_meta = pickle.loads(show.get('kodi_meta'))
        title = kodi_meta.get('name')
        title = self._clean_title(title)
        headers = {'Referer': self._BASE_URL}
        params = {'keyword': title,
                  'id': -1,
                  'link_web': self._BASE_URL}
        r = database.get(
            self._get_request,
            8,
            'https://ajax.gogo-load.com/site/loadAjaxSearch',
            data=params,
            headers=headers
        )
        r = json.loads(r).get('content')

        if not r and ':' in title:
            title = title.split(':')[0]
            params.update({'keyword': title})
            r = database.get(
                self._get_request,
                8,
                'https://ajax.gogo-load.com/site/loadAjaxSearch',
                data=params,
                headers=headers
            )
            r = json.loads(r).get('content')

        soup = BeautifulSoup(r, 'html.parser')
        items = soup.find_all('div', {'class': 'list_search_ajax'})
        if len(items) == 1:
            slugs = [items[0].find('a').get('href').split('/')[-1]]
        else:
            slugs = [
                item.find('a').get('href').split('/')[-1]
                for item in items
                if ((item.a.text.strip() + '  ').lower()).startswith((title + '  ').lower())
                or ((item.a.text.strip() + '  ').lower()).startswith((title + ' (Dub)  ').lower())
                or ((item.a.text.strip() + '  ').lower()).startswith((title + ' (TV)  ').lower())
                or ((item.a.text.strip() + '  ').lower()).startswith((title + ' (TV) (Dub)  ').lower())
                or ((item.a.text.strip().replace(' - ', ' ') + '  ').lower()).startswith((title + '  ').lower())
                or (item.a.text.strip().replace(':', ' ') + '   ').startswith(title + '   ')
            ]
        if not slugs:
            slugs = database.get(get_backup, 168, anilist_id, 'Gogoanime')
            if not slugs:
                return []
        slugs = list(slugs.keys()) if isinstance(slugs, dict) else slugs
        mapfunc = partial(self._process_gogo, show_id=anilist_id, episode=episode)
        all_results = list(map(mapfunc, slugs))
        all_results = list(itertools.chain(*all_results))
        return all_results

    def _process_gogo(self, slug, show_id, episode):
        url = "{0}{1}-episode-{2}".format(self._BASE_URL, slug, episode)
        headers = {'Referer': self._BASE_URL}
        title = (slug.replace('-', ' ')).title() + '  Episode-{0}'.format(episode)
        r = database.get(
            self._send_request,
            8,
            url,
            headers=headers
        )

        if not r:
            url = '{0}category/{1}'.format(self._BASE_URL, slug)
            html = database.get(
                self._send_request,
                8,
                url,
                headers=headers
            )
            mid = re.findall(r'value="([^"]+)"\s*id="movie_id"', html)
            if mid:
                params = {'ep_start': episode,
                          'ep_end': episode,
                          'id': mid[0],
                          'alias': slug}
                eurl = 'https://ajax.gogo-load.com/ajax/load-list-episode'
                r2 = self._get_request(eurl, data=params, headers=headers)
                soup2 = BeautifulSoup(r2, 'html.parser')
                eslug = soup2.find('a')
                if eslug:
                    eslug = eslug.get('href').strip()
                    url = "{0}{1}".format(self._BASE_URL[:-1], eslug)
                    r = self._send_request(url, headers=headers)

        soup = BeautifulSoup(r, 'html.parser')
        sources = []

        for element in soup.select('.anime_muti_link > ul > li'):
            server = element.get('class')[0]
            link = element.a.get('data-video')
            type_ = None
            quality = 'EQ'

            if server == 'vidcdn':
                type_ = 'embed'
                if link.startswith('//'):
                    link = 'https:' + link
            # elif server == 'xstreamcdn':
            #     type_ = 'embed'
            elif server == 'mp4upload':
                type_ = 'embed'
            elif server == 'doodstream':
                type_ = 'embed'
            # elif server == 'streamsb':
            #     type_ = 'embed'

            if not type_:
                continue

            source = {
                'release_title': title,
                'hash': link,
                'type': type_,
                'quality': quality,
                'debrid_provider': '',
                'provider': 'gogo',
                'size': 'NA',
                'info': source_utils.getInfo(slug) + [server],
                'lang': source_utils.getAudio_lang(title)
            }
            sources.append(source)

        return sources

    def get_latest(self):
        url = 'https://ajax.gogocdn.net/ajax/page-recent-release.html?page=1&type=1'
        return self._process_latest_view(url)

    def get_latest_dub(self):
        url = 'https://ajax.gogocdn.net/ajax/page-recent-release.html?page=1&type=2'
        return self._process_latest_view(url)

    def _process_latest_view(self, url):
        result = self._send_request(url)
        soup = BeautifulSoup(result, 'html.parser')
        animes = soup.find_all('div', {'class': 'img'})
        all_results = list(map(self._parse_latest_view, animes))
        return all_results

    def _parse_latest_view(self, res):
        res = res.a
        info = {}
        slug, episode = (res['href'][1:]).rsplit('-episode-')
        url = '%s/%s' % (slug, episode)
        name = '%s - Ep. %s' % (res['title'], episode)
        image = res.img['src']
        info['title'] = name
        info['mediatype'] = 'tvshow'
        return utils.allocate_item(name, "play_gogo/" + str(url), False, image, info)
