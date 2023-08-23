import json
import pickle
import re

from bs4 import BeautifulSoup, SoupStrainer
from six.moves import urllib_parse
from resources.lib.ui import control, database
from resources.lib.ui.jscrypto import jscrypto
from resources.lib.ui.BrowserBase import BrowserBase


class sources(BrowserBase):
    _BASE_URL = 'https://aniwatch.to/'
    keyurl = 'https://raw.githubusercontent.com/enimax-anime/key/e6/key.txt'
    keyhints = [[53, 59], [71, 78], [119, 126], [143, 150]]

    def get_sources(self, anilist_id, episode, get_backup):
        show = database.get_show(anilist_id)
        kodi_meta = pickle.loads(show.get('kodi_meta'))
        title = kodi_meta.get('name')
        title = self._clean_title(title)

        srcs = ['sub', 'dub']
        if control.getSetting('general.source') == 'Sub':
            srcs.remove('dub')
        elif control.getSetting('general.source') == 'Dub':
            srcs.remove('sub')

        headers = {'Referer': self._BASE_URL}
        params = {'keyword': title}
        res = database.get(
            self._get_request,
            8,
            self._BASE_URL + 'search',
            data=params,
            headers=headers
        )

        mlink = SoupStrainer('div', {'class': 'flw-item'})
        mdiv = BeautifulSoup(res, "html.parser", parse_only=mlink)
        sdivs = mdiv.find_all('h3')
        sitems = []
        for sdiv in sdivs:
            try:
                slug = sdiv.find('a').get('href').split('?')[0]
                stitle = sdiv.find('a').get('data-jname')
                sitems.append({'title': stitle, 'slug': slug})
            except AttributeError:
                pass

        all_results = []
        if sitems:
            if title[-1].isdigit():
                items = [x.get('slug') for x in sitems if title.lower() in x.get('title').lower()]
            else:
                items = [x.get('slug') for x in sitems if (title.lower() + '  ') in (x.get('title').lower() + '  ')]
            if not items and ':' in title:
                title = title.split(':')[0]
                items = [x.get('slug') for x in sitems if (title.lower() + '  ') in (x.get('title').lower() + '  ')]

            if items:
                slug = items[0]
                all_results = self._process_aw(slug, title=title, episode=episode, langs=srcs)
        return all_results

    def _process_aw(self, slug, title, episode, langs):
        sources = []
        headers = {'Referer': self._BASE_URL}
        r = database.get(
            self._get_request,
            8,
            self._BASE_URL + 'ajax/v2/episode/list/' + slug.split('-')[-1],
            headers=headers,
            XHR=True
        )
        res = json.loads(r).get('html')
        elink = SoupStrainer('div', {'class': re.compile('^ss-list')})
        ediv = BeautifulSoup(res, "html.parser", parse_only=elink)
        items = ediv.find_all('a')
        e_id = [x.get('data-id') for x in items if x.get('data-number') == episode]
        if e_id:
            params = {'episodeId': e_id[0]}
            r = database.get(
                self._get_request,
                8,
                self._BASE_URL + 'ajax/v2/episode/servers',
                data=params,
                headers=headers,
                XHR=True
            )
            eres = json.loads(r).get('html')
            for lang in langs:
                elink = SoupStrainer('div', {'class': re.compile('servers-{0}$'.format(lang))})
                sdiv = BeautifulSoup(eres, "html.parser", parse_only=elink)
                srcs = sdiv.find_all('div', {'class': 'item'})
                for src in srcs:
                    edata_id = src.get('data-id')
                    edata_name = src.text.strip().lower()
                    eserver_id = src.get('data-server-id')
                    if edata_name in ['megacloud', 'vidstreaming', 'streamtape']:
                        params = {'id': edata_id}
                        r = self._get_request(
                            self._BASE_URL + 'ajax/v2/episode/sources',
                            data=params,
                            headers=headers,
                            XHR=True
                        )
                        slink = json.loads(r).get('link')
                        if edata_name == 'streamtape':
                            source = {
                                'release_title': '{0} - Ep {1}'.format(title, episode),
                                'hash': slink,
                                'type': 'embed',
                                'quality': 'EQ',
                                'debrid_provider': '',
                                'provider': 'aniwatch',
                                'size': 'NA',
                                'info': ['DUB' if lang == 'dub' else 'SUB', edata_name],
                                'lang': 2 if lang == 'dub' else 0,
                            }
                            sources.append(source)
                        else:
                            headers = {'Referer': slink}
                            sl = urllib_parse.urlparse(slink)
                            spath = sl.path.split('/')
                            spath.insert(2, 'ajax')
                            sid = spath.pop(-1)
                            eurl = '{}://{}{}/getSources'.format(sl.scheme, sl.netloc, '/'.join(spath))
                            params = {'id': sid}
                            res = self._get_request(
                                eurl,
                                data=params,
                                headers=headers,
                                XHR=True
                            )
                            res = json.loads(res)
                            subs = res.get('tracks')
                            if subs:
                                subs = [{'url': x.get('file'), 'lang': x.get('label')} for x in subs if x.get('kind') == 'captions']
                            slink = self._process_link(res.get('sources'))
                            if not slink:
                                continue
                            res = self._get_request(slink, headers=headers)
                            quals = re.findall(r'#EXT.+?RESOLUTION=\d+x(\d+).+\n(?!#)(.+)', res)

                            for qual, qlink in quals:
                                qual = int(qual)
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
                                    'hash': urllib_parse.urljoin(slink, qlink) + '|User-Agent=iPad',
                                    'type': 'direct',
                                    'quality': quality,
                                    'debrid_provider': '',
                                    'provider': 'aniwatch',
                                    'size': 'NA',
                                    'info': ['DUB' if lang == 'dub' else 'SUB', 'Server ' + eserver_id],
                                    'lang': 2 if lang == 'dub' else 0,
                                    'subs': subs
                                }
                                sources.append(source)
        return sources

    def _process_link(self, sources):
        r = database.get(
            self._get_request,
            4,
            self.keyurl
        )
        keyhints = json.loads(r) or self.keyhints
        key = ''
        orig_src = sources
        try:
            for start, end in keyhints:
                key += orig_src[start:end]
                sources = sources.replace(orig_src[start:end], '')
            if 'file' not in sources:
                sources = json.loads(jscrypto.decode(sources, key))
            return sources[0].get('file')
        except:
            database.remove(
                self._get_request,
                self.keyurl
            )
            control.log('decryption key not working')
            return ''
