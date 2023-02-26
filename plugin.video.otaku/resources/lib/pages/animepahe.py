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
            'animepahe'
        )

        if r and r.get('sources'):
            srcs = r.get('sources')
            quals = []
            for i in range(len(srcs)):
                src = srcs[i]
                if src.get('quality') in quals:
                    srcs[i].update({'type': 'DUB'})
                else:
                    quals.append(src.get('quality'))
                    srcs[i].update({'type': 'SUB'})
            referer = r.get('headers', {}).get('Referer', '')
            mapfunc = partial(self._process_ap, title=title, referer=referer)
            all_results = list(map(mapfunc, srcs))
            all_results = list(itertools.chain(*all_results))

        return all_results

    def _process_ap(self, item, title='', referer=''):
        sources = []
        slink = item.get('url') + '|Referer={0}&User-Agent=iPad'.format(referer)
        qual = int(item.get('quality'))
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
            'provider': 'animepahe',
            'size': self._get_size(item.get('size', 0)),
            'info': [item.get('type'), 'HLS' if item.get('isM3U8') else ''],
            'lang': 0 if item.get('type') == 'SUB' else 2
        }
        sources.append(source)
        return sources
