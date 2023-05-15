import json
import pickle
import re
import six

from kodi_six import xbmc
from functools import partial
from resources.lib.ui import client, control, database, utils


class CONSUMETAPI:
    def __init__(self):
        self.baseUrl = 'https://api.consumet.org/'
        self.baseUrl2 = control.getSetting('consumet.hosting.menu').rstrip('/') + '/'
        self.episodesUrl = 'meta/anilist/episodes/{0}?provider={1}'
        self.episodesUrl2 = 'meta/anilist/info/{0}?provider={1}'
        self.streamUrl = 'anime/{0}/watch/{1}'
        self.streamUrl2 = 'anime/{0}/watch?episodeId={1}'
        self.synurl = 'https://find-my-anime.dtimur.de/api?id={0}&provider=Anilist'
        self.hosting = control.getSetting('consumet.hosting.bool') == 'true'

    def _json_request(self, url):
        if self.hosting:
            if not url.startswith('http'):
                url = self.baseUrl2 + url
            ratelimited = True
            retries = 3
        else:
            if not url.startswith('http'):
                url = self.baseUrl + url
            ratelimited = True
            retries = 3
        while ratelimited and retries > 0:
            response = database.get(
                client.request,
                4,
                url,
                error=True,
                output='extended',
                timeout=10
            )
            data = {}
            if response and int(response[1]) < 300:
                data = json.loads(response[0])
                if 'ratelimited' in data.get('message', ''):
                    database.remove(
                        client.request,
                        url,
                        error=True,
                        output='extended'
                    )
                    xbmc.sleep(5000)
                    retries -= 1
                else:
                    ratelimited = False
            else:
                ratelimited = False
        return data

    def _parse_episode_view(self, res, show_id, show_meta, season, poster, fanart, eps_watched, update_time):
        url = "%s/%s/" % (show_id, res['number'])
        name = res.get('title')
        image = res.get('image')

        info = {}
        info['plot'] = res.get('description', '')
        info['title'] = res.get('title', '')
        info['season'] = int(season)
        info['episode'] = res['number']
        try:
            if int(eps_watched) >= res['number']:
                info['playcount'] = 1
        except:
            pass
        info['aired'] = res.get('airDate')[:10] if res.get('airDate') else ''

        info['tvshowtitle'] = pickle.loads(database.get_show(show_id)['kodi_meta'])['title_userPreferred']
        info['mediatype'] = 'episode'
        parsed = utils.allocate_item(name, "play/" + str(url), False, image, info, fanart, poster)
        database._update_episode(show_id, season=season, number=res['number'], update_time=update_time, kodi_meta=parsed, air_date=info['aired'])
        return parsed

    def _get_season(self, res):
        regexes = [r'season\s(\d+)', r'\s(\d+)st\sseason\s', r'\s(\d+)nd\sseason\s',
                   r'\s(\d+)rd\sseason\s', r'\s(\d+)th\sseason\s']
        s_ids = []
        for regex in regexes:
            if isinstance(res.get('title'), dict):
                s_ids += [re.findall(regex, name, re.IGNORECASE) for lang, name in six.iteritems(res.get('title')) if name is not None]
            else:
                s_ids += [re.findall(regex, name, re.IGNORECASE) for name in res.get('title')]
            s_ids += [re.findall(regex, name, re.IGNORECASE) for name in res.get('synonyms')]
        s_ids = [s[0] for s in s_ids if s]
        if not s_ids:
            regex = r'\s(\d+)$'
            cour = False
            if isinstance(res.get('title'), dict):
                for lang, name in six.iteritems(res.get('title')):
                    if name is not None and (' part ' in name.lower() or ' cour ' in name.lower()):
                        cour = True
                        break
                if not cour:
                    s_ids += [re.findall(regex, name, re.IGNORECASE) for lang, name in six.iteritems(res.get('title')) if name is not None]
                    s_ids += [re.findall(regex, name, re.IGNORECASE) for name in res.get('synonyms')]
            else:
                for name in res.get('title'):
                    if ' part ' in name.lower() or ' cour ' in name.lower():
                        cour = True
                        break
                if not cour:
                    s_ids += [re.findall(regex, name, re.IGNORECASE) for name in res.get('title')]
                    s_ids += [re.findall(regex, name, re.IGNORECASE) for name in res.get('synonyms')]
            s_ids = [s[0] for s in s_ids if s]

        return s_ids

    def _process_episode_view(self, anilist_id, show_meta, poster, fanart, eps_watched):
        from datetime import date
        update_time = date.today().isoformat()
        all_results = []
        result = self.get_anilist_meta(anilist_id)
        if result:
            season = 1
            s_id = self._get_season(result)
            # if not s_id:
            #     res = self._json_request(self.synurl.format(anilist_id))
            #     if res:
            #         s_id = self._get_season(res[0])
            if s_id:
                season = s_id[0]
            result = result.get('episodes')
            mapfunc = partial(self._parse_episode_view, show_id=anilist_id, show_meta=show_meta, season=season, poster=poster, fanart=fanart, eps_watched=eps_watched, update_time=update_time)
            all_results = list(map(mapfunc, result))
        return all_results

    def _parse_episodes(self, res, show_id, eps_watched):
        parsed = pickle.loads(res['kodi_meta'])

        try:
            if int(eps_watched) >= res['number']:
                parsed['info']['playcount'] = 1
        except:
            pass

        return parsed

    def _process_episodes(self, anilist_id, episodes, eps_watched):
        mapfunc = partial(self._parse_episodes, show_id=anilist_id, eps_watched=eps_watched)
        all_results = list(map(mapfunc, episodes))

        return all_results

    def get_anilist_meta(self, anilist_id):
        url = 'meta/anilist/info/{0}'.format(anilist_id)
        return self._json_request(url)

    def get_episodes(self, anilist_id, filter_lang):
        show_meta = database.get_show_meta(anilist_id)
        meta_ids = pickle.loads(show_meta.get('meta_ids'))
        kodi_meta = pickle.loads(database.get_show(anilist_id).get('kodi_meta'))
        kodi_meta.update(pickle.loads(show_meta.get('art')))
        fanart = kodi_meta.get('fanart')
        poster = kodi_meta.get('poster')
        eps_watched = kodi_meta.get('eps_watched')
        episodes = database.get_episode_list(int(anilist_id))

        if episodes:
            return (self._process_episodes(anilist_id, episodes, eps_watched), 'episodes')

        return (self._process_episode_view(anilist_id, meta_ids, poster, fanart, eps_watched), 'episodes')

    def get_sources(self, anilist_id, episode, provider, lang=None):
        sources = []
        if provider in ['animepahe']:
            eurl = self.episodesUrl.format(anilist_id, provider)
        else:
            eurl = self.episodesUrl2.format(anilist_id, provider)
        if provider in ['gogoanime', '9anime', 'animesaturn']:
            eurl += '&{0}=true'.format(lang)
        episodes = self._json_request(eurl).get('episodes')
        if episodes:
            if episodes[0].get('number') != 1:
                episode = episodes[0].get('number') - 1 + int(episode)
            episode_id = [x.get('id') for x in episodes if x.get('number') == int(episode)][0]
            if provider == 'zoro' and lang == 'dub':
                episode_id = episode_id.replace('$sub', '$dub')
            surl = self.streamUrl if provider in ['animepahe', 'animesaturn', 'gogoanime', '9anime'] else self.streamUrl2
            sources = self._json_request(surl.format(provider, episode_id))

        return sources
