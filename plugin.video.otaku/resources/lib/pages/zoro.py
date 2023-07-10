import itertools
import pickle
from functools import partial

from resources.lib.ui import control, database
from resources.lib.ui.BrowserBase import BrowserBase
from resources.lib.indexers import anify, enime


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
                anify.ANIFYAPI().get_sources,
                8,
                anilist_id,
                episode,
                'zoro',
                x
            )

            if r and r.get('sources'):
                srcs = r.get('sources')
                subs = r.get('subtitles')
                if subs:
                    subs = [x for x in subs if x.get('lang') != 'Thumbnails']
                mapfunc = partial(self._process_ap, title=title, lang=2 if x == 'dub' else 0, subs=subs)
                results = list(map(mapfunc, srcs))
                results = list(itertools.chain(*results))
                all_results += results

        if not all_results:
            r = database.get(
                enime.ENIMEAPI().get_sources,
                8,
                anilist_id,
                episode,
                'zoro'
            )
            if r and r.get('url'):
                slink = r.get('url') + '|Referer={0}&User-Agent=iPad'.format(r.get('referer').split('?')[0])
                source = {
                    'release_title': title,
                    'hash': slink,
                    'type': 'direct',
                    'quality': 'EQ',
                    'debrid_provider': '',
                    'provider': 'zoro',
                    'size': 'NA',
                    'info': ['HLS'],
                    'lang': 0
                }
                if r.get('subtitle'):
                    source.update({'subs': [{'url': r.get('subtitle'), 'lang': 'English'}]})

                all_results.append(source)

        return all_results

    def _process_ap(self, item, title='', lang=0, subs=[]):
        sources = []
        quality = 'EQ'
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
            'info': ['DUB' if lang == 2 else 'SUB'],
            'lang': lang,
            'subs': subs
        }
        sources.append(source)
        return sources
