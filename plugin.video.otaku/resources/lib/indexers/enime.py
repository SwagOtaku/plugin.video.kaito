import json
import pickle

from functools import partial

from resources.lib.ui import client, control, database, utils


class ENIMEAPI:
    def __init__(self):
        self.baseUrl = 'https://api.enime.moe/'
        self.episodesUrl = 'mapping/anilist/{0}'
        self.streamUrl = 'source/{0}'

    def _json_request(self, url):
        url = self.baseUrl + url
        response = client.request(url)
        if response:
            response = json.loads(response)
        return response

    @staticmethod
    def _parse_episode_view(res, show_id, title_userpreferred, season, poster, fanart, eps_watched, update_time,
                            title_disable):
        url = "%s/%s/" % (show_id, res['number'])

        name = res.get('title')
        image = res.get('image')

        info = {
            'plot': res.get('description', ''),
            'title': res.get('title', ''),
            'season': int(season),
            'episode': res['number'],
            'tvshowtitle': title_userpreferred,
            'mediatype': 'episode'
        }

        try:
            if int(eps_watched) >= res['number']:
                info['playcount'] = 1
        except:
            pass

        try:
            info['aired'] = res['airedAt'][:10]
        except (KeyError, TypeError):
            info['aired'] = ''

        parsed = utils.allocate_item(name, "play/%s" % url, False, image, info, fanart, poster)
        database._update_episode(show_id, season=season, number=res['number'], update_time=update_time,
                                 kodi_meta=parsed, air_date=info['aired'])

        if title_disable and info.get('playcount') != 1:
            parsed['info']['title'] = 'Episode %s' % res["number"]
            parsed['info']['plot'] = "None"

        return parsed

    def _process_episode_view(self, anilist_id, title_userpreferred, poster, fanart, eps_watched, title_disable=False):
        from datetime import date
        update_time = date.today().isoformat()

        all_results = []
        result = self.get_anilist_meta(anilist_id)
        if result:
            season = 1
            s_id = utils.get_season(result)
            if s_id:
                season = s_id[0]
            database._update_season(anilist_id, season)

            result = result.get('episodes')
            mapfunc = partial(self._parse_episode_view, show_id=anilist_id, title_userpreferred=title_userpreferred,
                              season=season, poster=poster, fanart=fanart, eps_watched=eps_watched,
                              update_time=update_time, title_disable=title_disable)
            all_results = list(map(mapfunc, result))
        return all_results

    def append_episodes(self, anilist_id, title_userpreferred, episodes, eps_watched, poster, fanart, title_disable=False):
        import datetime
        import time
        update_time = datetime.date.today().isoformat()
        last_updated = datetime.datetime(*(time.strptime(episodes[0]['last_updated'], "%Y-%m-%d")[0:6]))
        diff = (datetime.datetime.today() - last_updated).days

        result = self.get_anilist_meta(anilist_id) if diff > 0 else {}
        if len(result) > len(episodes):
            season = database.get_season_list(anilist_id)['season']
            result = result.get('episodes')
            mapfunc2 = partial(self._parse_episode_view, show_id=anilist_id, title_userpreferred=title_userpreferred,
                               season=season, poster=poster, fanart=fanart, eps_watched=eps_watched,
                               update_time=update_time, title_disable=title_disable)
            all_results = list(map(mapfunc2, result))
        else:
            mapfunc1 = partial(self._parse_episodes, eps_watched=eps_watched,
                               title_disable=title_disable)
            all_results = list(map(mapfunc1, episodes))

        return all_results

    @staticmethod
    def _parse_episodes(res, eps_watched, title_disable=False):
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

    def _process_episodes(self, episodes, eps_watched, title_disable=False):
        mapfunc = partial(self._parse_episodes, eps_watched=eps_watched, title_disable=title_disable)
        all_results = list(map(mapfunc, episodes))
        return all_results

    def get_anilist_meta(self, anilist_id):
        url = 'mapping/anilist/{0}'.format(anilist_id)
        return self._json_request(url)

    def get_anilist_mapping(self, anilist_id):
        url = 'mapping/anilist/{0}'.format(anilist_id)
        return self._json_request(url)

    def get_episodes(self, anilist_id, filter_lang):
        show_meta = database.get_show_meta(anilist_id)
        kodi_meta = pickle.loads(database.get_show(anilist_id).get('kodi_meta'))
        if show_meta:
            kodi_meta.update(pickle.loads(show_meta.get('art')))
        #     meta_ids = pickle.loads(show_meta.get('meta_ids'))
        #
        # else:
        #     meta_ids = {}

        fanart = kodi_meta.get('fanart')
        poster = kodi_meta.get('poster')
        eps_watched = kodi_meta.get('eps_watched')
        title_userpreferred = kodi_meta['title_userPreferred']

        episodes = database.get_episode_list(int(anilist_id))
        title_disable = control.getSetting('general.spoilers') == 'true'

        if episodes:
            if kodi_meta['status'] != "FINISHED":
                return self.append_episodes(anilist_id, title_userpreferred, episodes, eps_watched, poster, fanart, title_disable), 'episodes'
            return self._process_episodes(episodes, eps_watched, title_disable), 'episodes'

        return self._process_episode_view(anilist_id, title_userpreferred, poster, fanart, eps_watched, title_disable), 'episodes'

    def get_sources(self, anilist_id, episode, provider, lang=None):
        sources = []
        eurl = self.episodesUrl.format(anilist_id)
        episodes = self._json_request(eurl).get('episodes')
        if episodes:
            episodes = sorted(episodes, key=lambda x: x.get('number'))
            if episodes[0].get('number') != 1:
                episode = episodes[0].get('number') - 1 + int(episode)
            episode_srcs = [x.get('sources') for x in episodes if x.get('number') == int(episode)][0]
            episode_id = episode_srcs[0].get('id') if provider == 'gogoanime' else episode_srcs[1].get('id')
            sources = self._json_request(self.streamUrl.format(episode_id))

        return sources
