import re
import itertools
import pickle

from functools import partial
from bs4 import BeautifulSoup
from resources.lib.ui.BrowserBase import BrowserBase
from resources.lib.ui import database, source_utils, client
from resources.lib import debrid


class sources(BrowserBase):
    _BASE_URL = 'https://animetosho.org'

    def get_sources(self, query, anilist_id, episode, status, media_type, rescrape):
        query = self._clean_title(query)
        query = self._sphinx_clean(query)

        if rescrape:
            # todo add rescrape stuff here
            pass
            # return self._get_episode_sources_pack(quary, anilist_id, episode)
        if media_type != "movie":
            query = '%s "\- %s"' % (query, episode.zfill(2))  # noQA
            season = database.get_season_list(anilist_id)['season']
            season = str(season).zfill(2)
            query += '|"S%sE%s "' % (season, episode.zfill(2))
        else:
            season = None
        rex = r'(magnet:)+[^"]*'

        show_meta = database.get_show_meta(anilist_id)
        params = {
            'q': query,
            'qx': 1
        }
        if show_meta:
            meta_ids = pickle.loads(show_meta['meta_ids'])
            if meta_ids.get('anidb'):
                params.update({'aids': meta_ids.get('anidb')})

        html = client.request(self._BASE_URL + '/search', params=params)
        soup = BeautifulSoup(html, "html.parser")
        soup_all = soup.find('div', id='content').find_all('div', class_='home_list_entry')
        list_ = [
            {'name': soup.find('div', class_='link').a.text,
             'magnet': soup.find('a', {'href': re.compile(rex)}).get('href'),
             'size': soup.find('div', class_='size').text,
             'downloads': 0,
             'torrent': soup.find('a', class_='dllink').get('href')
             }
            for soup in soup_all
        ]

        regex = r'\ss(\d+)|season\s(\d+)|(\d+)+(?:st|[nr]d|th)\sseason'
        regex_ep = r'\de(\d+)\b|\se(\d+)\b|\s-\s(\d{1,3})\b'
        rex = re.compile(regex)
        rex_ep = re.compile(regex_ep)

        filtered_list = []
        for torrent in list_:
            try:
                torrent['hash'] = re.match(r'https://animetosho.org/storage/torrent/([^/]+)', torrent['torrent']).group(1)
            except AttributeError:
                continue
            if season:
                title = torrent['name'].lower()

                ep_match = rex_ep.findall(title)
                ep_match = list(map(int, list(filter(None, itertools.chain(*ep_match)))))

                if ep_match and ep_match[0] != int(episode):
                    regex_ep_range = r'\s\d+-\d+|\s\d+~\d+|\s\d+\s-\s\d+|\s\d+\s~\s\d+'
                    rex_ep_range = re.compile(regex_ep_range)

                    if not rex_ep_range.search(title):
                        continue

                match = rex.findall(title)
                match = list(map(int, list(filter(None, itertools.chain(*match)))))

                if not match or match[0] == int(season):
                    filtered_list.append(torrent)

            else:
                filtered_list.append(torrent)
        cache_list = debrid.TorrentCacheCheck().torrentCacheCheck(filtered_list)
        mapfunc = partial(parse_animetosho_view, episode=episode)
        all_results = list(map(mapfunc, cache_list))
        return all_results


def parse_animetosho_view(res, episode):
    source = {
        'release_title': res['name'],
        'hash': res['hash'],
        'type': 'torrent',
        'quality': source_utils.getQuality(res['name']),
        'debrid_provider': res['debrid_provider'],
        'provider': 'animetosho',
        'episode_re': episode,
        'size': res['size'],
        'info': source_utils.getInfo(res['name']),
        'lang': source_utils.getAudio_lang(res['name'])
    }
    return source
