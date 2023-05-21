import itertools
import pickle
from functools import partial
from six.moves import urllib_parse

from resources.lib.ui import control, database
from resources.lib.ui.BrowserBase import BrowserBase
from resources.lib.indexers import consumet, enime


class sources(BrowserBase):
    def get_sources(self, anilist_id, episode, get_backup):
        all_results = []
        show = database.get_show(anilist_id)
        kodi_meta = pickle.loads(show.get('kodi_meta'))
        title = kodi_meta.get('ename') or kodi_meta.get('name')
        title = self._clean_title(title)
        title = '{0} Ep-{1}'.format(title, episode)
        srcs = ['sub', 'dub']
        if control.getSetting('general.source') == 'Sub':
            srcs.remove('dub')
        elif control.getSetting('general.source') == 'Dub':
            srcs.remove('sub')

        for x in srcs:
            r = database.get(
                consumet.CONSUMETAPI().get_sources,
                8,
                anilist_id,
                episode,
                'gogoanime',
                x
            )

            if r and r.get('sources'):
                srcs = r.get('sources')
                for i in range(len(srcs)):
                    srcs[i].update({'type': x.upper()})
                referer = r.get('headers', {}).get('Referer', '')
                if referer:
                    referer = urllib_parse.urljoin(referer, '/')
                mapfunc = partial(self._process_ap, title=title, referer=referer)
                results = list(map(mapfunc, srcs))
                results = list(itertools.chain(*results))
                all_results += results

        if not all_results:
            r = database.get(
                enime.ENIMEAPI().get_sources,
                8,
                anilist_id,
                episode,
                'gogoanime'
            )
            if r and r.get('url'):
                slink = r.get('url') + '|Referer={0}&User-Agent=iPad'.format(r.get('referer').split('?')[0])
                source = {
                    'release_title': title,
                    'hash': slink,
                    'type': 'direct',
                    'quality': 'EQ',
                    'debrid_provider': '',
                    'provider': 'gogohd',
                    'size': 'NA',
                    'info': ['HLS'],
                    'lang': 0
                }
                all_results.append(source)

        return all_results

    def _process_ap(self, item, title='', referer=''):
        sources = []
        quality = 'EQ'
        slink = item.get('url') + '|Referer={0}&User-Agent=iPad'.format(referer)
        qual = item.get('quality')
        if qual.endswith('0p'):
            qual = int(qual[:-1])
            if qual < 361:
                quality = 'EQ'
            elif qual < 577:
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
            'provider': 'gogohd',
            'size': 'NA',
            'info': [item.get('type'), 'HLS' if item.get('isM3U8') else ''],
            'lang': 0 if item.get('type') == 'SUB' else 2
        }
        sources.append(source)
        return sources
