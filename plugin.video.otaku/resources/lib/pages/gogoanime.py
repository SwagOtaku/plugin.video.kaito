import bs4 as bs
import itertools
from functools import partial
from resources.lib.ui import utils, source_utils, database, control
from resources.lib.ui.BrowserBase import BrowserBase
import requests
import re
import ast


class sources(BrowserBase):
    def get_sources(self, anilist_id, episode, get_backup):
        slugs = database.get(get_backup, 168, anilist_id, 'Gogoanime')
        if not slugs:
            show = database.get_show(anilist_id)
            kodi_meta = ast.literal_eval(show.get('kodi_meta'))
            title = kodi_meta.get('name').lower()
            title = re.sub(r"[^a-z0-9- ]", '', title).replace(' -', '').replace(' ', '-')
            slugs = [title, title + '-dub']
        slugs = list(slugs.keys()) if isinstance(slugs, dict) else slugs
        mapfunc = partial(self._process_gogo, show_id=anilist_id, episode=episode)
        all_results = list(map(mapfunc, slugs))
        all_results = list(itertools.chain(*all_results))
        return all_results

    def _process_gogo(self, slug, show_id, episode):
        url = "https://gogoanime.ee/%s-episode-%s" % (slug, episode)
        title = (slug.replace('-', ' ')).title()
        result = requests.get(url).text
        soup = bs.BeautifulSoup(result, 'html.parser')
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
        soup = bs.BeautifulSoup(result, 'html.parser')
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
