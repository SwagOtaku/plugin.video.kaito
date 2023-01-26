import itertools
import pickle
from functools import partial

from resources.lib.ui import database
from resources.lib.ui.BrowserBase import BrowserBase
from resources.lib.indexers import consumet


class sources(BrowserBase):
    def get_sources(self, anilist_id, episode, get_backup):
        all_results = []
        show = database.get_show(anilist_id)
        kodi_meta = pickle.loads(show.get('kodi_meta'))
        title = kodi_meta.get('ename') or kodi_meta.get('name')
        title = self._clean_title(title)
        title = '{0} Ep-{1}'.format(title, episode)

        r = database.get(
            consumet.CONSUMETAPI().get_sources,
            8,
            anilist_id,
            episode,
            'zoro',
            'dub'
        )

        if r.get('sources'):
            srcs = r.get('sources')
            mapfunc = partial(self._process_ap, title=title, lang=2)
            all_results = list(map(mapfunc, srcs))
            all_results = list(itertools.chain(*all_results))

        return all_results

    def _process_ap(self, item, title='', lang=0):
        sources = []
        slink = item.get('url')
        qual = item.get('quality')
        if qual.endswith('p'):
            qual = int(qual[:-1])
            if qual < 577:
                quality = 'NA'
            elif qual < 721:
                quality = '720p'
            elif qual < 1081:
                quality = '1080p'
            else:
                quality = '4K'

            source = {
                'release_title': title,
                'hash': slink,
                'type': 'direct',
                'quality': quality,
                'debrid_provider': '',
                'provider': 'zoro',
                'size': 'NA',
                'info': ['DUB' if lang == 2 else 'SUB', 'HLS' if item.get('isM3U8') else ''],
                'lang': lang
            }
            sources.append(source)
        return sources
