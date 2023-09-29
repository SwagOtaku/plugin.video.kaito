import json
import pickle

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

    def _parse_episode_view(self, res, show_id, show_meta, season, poster, fanart, eps_watched, update_time, title_disable):
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

        if title_disable and info.get('playcount') != 1:
            parsed['info']['title'] = 'Episode %s' % res["number"]
            parsed['info']['plot'] = "None"

        return parsed

    def _process_episode_view(self, anilist_id, show_meta, poster, fanart, eps_watched, title_disable=False):
        from datetime import date
        update_time = date.today().isoformat()

        all_results = []
        result = self.get_anilist_meta(anilist_id)
        if result:
            season = 1
            s_id = utils.get_season(result)
            if s_id:
                season = s_id[0]

            result = result.get('episodes')
            database._update_season(anilist_id, season)

            mapfunc = partial(self._parse_episode_view, show_id=anilist_id, show_meta=show_meta, season=season,
                              poster=poster, fanart=fanart, eps_watched=eps_watched, update_time=update_time,
                              title_disable=title_disable)
            all_results = list(map(mapfunc, result))
        return all_results

    @staticmethod
    def _parse_episodes(res, show_id, eps_watched, title_disable=False):
        parsed = pickle.loads(res['kodi_meta'])

        try:
            if int(eps_watched) >= res['number']:
                parsed['info']['playcount'] = 1
        except:
            pass

        if title_disable and parsed['info'].get('playcount') != 1:
            parsed['info']['title'] = 'Episode %s' % res["number"]
            parsed['info']['plot'] = "None"

        return parsed

    def process_episodes(self, anilist_id, episodes, eps_watched, title_disable=False):
        mapfunc = partial(self._parse_episodes, show_id=anilist_id, eps_watched=eps_watched, title_disable=title_disable)
        all_results = list(map(mapfunc, episodes))

        return all_results

    def get_anilist_meta(self, anilist_id):
        url = 'meta/anilist/info/{0}'.format(anilist_id)
        return self._json_request(url)

    def get_episodes(self, anilist_id, filter_lang):
        show_meta = database.get_show_meta(anilist_id)
        kodi_meta = pickle.loads(database.get_show(anilist_id).get('kodi_meta'))
        if show_meta:
            kodi_meta.update(pickle.loads(show_meta.get('art')))
            meta_ids = pickle.loads(show_meta.get('meta_ids'))
        else:
            meta_ids = {}
        fanart = kodi_meta.get('fanart')
        poster = kodi_meta.get('poster')
        eps_watched = kodi_meta.get('eps_watched')
        episodes = database.get_episode_list(int(anilist_id))

        title_disable = control.getSetting('general.spoilers') == 'true'

        if episodes:
            return self.process_episodes(anilist_id, episodes, eps_watched, title_disable), 'episodes'

        return self._process_episode_view(anilist_id, meta_ids, poster, fanart, eps_watched, title_disable), 'episodes'

    def get_sources(self, anilist_id, episode, provider, lang=None):
        sources = []
        if provider in ['animepahe']:
            eurl = self.episodesUrl.format(anilist_id, provider)
        else:
            eurl = self.episodesUrl2.format(anilist_id, provider)
        if provider in ['gogoanime', '9anime']:
            eurl += '&{0}=true'.format(lang)
        episodes = self._json_request(eurl).get('episodes')
        if episodes:
            episodes = sorted(episodes, key=lambda x: x.get('number'))
            if episodes[0].get('number') != 1:
                episode = episodes[0].get('number') - 1 + int(episode)
            episode_id = [x.get('id') for x in episodes if x.get('number') == int(episode)][0]
            surl = self.streamUrl if provider in ['animepahe', 'gogoanime', '9anime'] else self.streamUrl2
            sources = self._json_request(surl.format(provider, episode_id))

        return sources
