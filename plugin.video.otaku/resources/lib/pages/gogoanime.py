from bs4 import BeautifulSoup
import itertools
from functools import partial
from resources.lib.ui import utils, source_utils, database
from resources.lib.ui.BrowserBase import BrowserBase
import re
import requests
import ast


class sources(BrowserBase):
    def get_sources(self, anilist_id, episode, get_backup):
        show = database.get_show(anilist_id)
        kodi_meta = ast.literal_eval(show.get('kodi_meta'))
        title = kodi_meta.get('name')
        hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
                'Referer': 'https://gogoanime.tel/'}
        params = {'keyword': title,
                  'id': -1,
                  'link_web': 'https://gogoanime.tel/'}
        r = requests.get('https://ajax.gogo-load.com/site/loadAjaxSearch', headers=hdrs, params=params).json()
        soup = BeautifulSoup(r.get('content'), 'html.parser')
        items = soup.find_all('div', {'class': 'list_search_ajax'})
        slugs = [
            item.find('a').get('href').split('/')[-1]
            for item in items
            if (item.text.strip() + ' ').startswith(title + ' ')
            or (item.text.strip().replace(' - ', ' ') + ' ').startswith(title + ' ')
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
        url = "https://gogoanime.tel/{0}-episode-{1}".format(slug, episode)
        title = (slug.replace('-', ' ')).title() + '  Episode-{0}'.format(episode)
        hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
                'Referer': 'https://gogoanime.tel/'}
        r = requests.get(url, headers=hdrs)
        if r.status_code > 400:
            url = 'https://gogoanime.tel/category/{0}'.format(slug)
            html = requests.get(url, headers=hdrs).text
            mid = re.findall(r'value="([^"]+)"\s*id="movie_id"', html)
            if mid:
                params = {'ep_start': episode,
                          'ep_end': episode,
                          'id': mid[0],
                          'alias': slug}
                eurl = 'https://ajax.gogo-load.com/ajax/load-list-episode'
                r2 = requests.get(eurl, headers=hdrs, params=params)
                soup2 = BeautifulSoup(r2.text, 'html.parser')
                eslug = soup2.find('a')
                if eslug:
                    eslug = eslug.get('href').strip()
                    url = "https://gogoanime.tel{0}".format(eslug)
                    r = requests.get(url, headers=hdrs)

        soup = BeautifulSoup(r.text, 'html.parser')
        sources = []

        for element in soup.select('.anime_muti_link > ul > li'):
            server = element.get('class')[0]
            link = element.a.get('data-video')
            type_ = None
            quality = 'NA'

            if server == 'xstreamcdn':
                type_ = 'embed'
                quality = '1080p'
            elif server == 'vidcdn':
                type_ = 'embed'
                link = 'https:' + link
            elif server == 'mp4upload':
                type_ = 'embed'
            # elif server == 'doodstream':
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
                'info': source_utils.getInfo(slug),
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
        result = requests.get(url).text
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
