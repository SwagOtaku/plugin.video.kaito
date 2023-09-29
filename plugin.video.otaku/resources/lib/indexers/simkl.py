import json
import pickle
import random

from functools import partial
from resources.lib.ui import client, database, utils, control
from resources.lib.indexers.syncurl import SyncUrl


class SIMKLAPI:
    def __init__(self):
        self.ClientID = "5178a709b7942f1f5077b737b752eea0f6dee684d0e044fa5acee8822a0cbe9b"
        self.baseUrl = "https://api.simkl.com/"
        self.imagePath = "https://wsrv.nl/?url=https://simkl.in/episodes/%s_w.webp"

    def _to_url(self, url=''):
        if url.startswith("/"):
            url = url[1:]
        return "%s/%s" % (self.baseUrl[:-1], url)

    @staticmethod
    def _json_request(url, data=''):
        response = database.get(client.request, 4, url, params=data, error=True)
        response = json.loads(response)
        return response

    def _parse_episode_view(self, res, anilist_id, season, poster, fanart, eps_watched, update_time, tvshowtitle,
                            filter_lang, title_disable):

        url = "%s/%s/" % (anilist_id, res['episode'])

        if isinstance(fanart, list):
            fanart = random.choice(fanart)
        if filter_lang:
            url += filter_lang

        title = res.get('title')
        if not title:
            title = "Episode %s" % res["episode"]

        image = self.imagePath % res['img'] if res.get('img') else poster

        info = {
            'plot': res.get('description', ''),
            'title': res['title'],
            'season': season,
            'episode': int(res['episode']),
            'tvshowtitle': tvshowtitle,
            'mediatype': 'episode'
        }

        if eps_watched:
            if int(eps_watched) >= res['episode']:
                info['playcount'] = 1

        try:
            info['aired'] = res['date'][:10]
        except:
            pass

        parsed = utils.allocate_item(title, "play/%s" % url, False, image, info, fanart, poster)
        database._update_episode(anilist_id, season, res['episode'], '', update_time, parsed)

        if title_disable and info.get('playcount') != 1:
            parsed['info']['title'] = 'Episode %s' % res["episode"]
            parsed['info']['plot'] = "None"

        return parsed

    def _process_episode_view(self, anilist_id, poster, fanart, eps_watched, tvshowtitle, filter_lang, title_disable):
        from datetime import date
        update_time = date.today().isoformat()
        result = database.get(self.get_anime_info, 6, anilist_id)
        result_ep = database.get(self.get_anilist_meta, 6, anilist_id)

        season = result.get('season')

        sync_data = SyncUrl().get_anime_data(anilist_id, 'Anilist')
        s_id = utils.get_season(sync_data[0])
        season = s_id[0] if s_id else 1

        season = int(season)
        database._update_season(anilist_id, season)

        result_ep = [x for x in result_ep if x['type'] == 'episode']

        mapfunc = partial(self._parse_episode_view, anilist_id=anilist_id, season=season, poster=poster, fanart=fanart,
                          eps_watched=eps_watched, filter_lang=filter_lang, update_time=update_time,
                          tvshowtitle=tvshowtitle, title_disable=title_disable)
        all_results = list(map(mapfunc, result_ep))

        if len(all_results) == 0 or control.getSetting('simkl.unaired') == 'true':
            total_ep = result.get('total_episodes', 0)
            empty_ep = []
            for ep in range(len(all_results) + 1, total_ep + 1):
                empty_ep.append({
                    # 'title': control.colorString('Episode %s' % ep, 'red'),
                    'title': 'Episode %s' % ep,
                    'episode': ep,
                    'image': poster
                })
            mapfunc_emp = partial(self._parse_episode_view, anilist_id=anilist_id, season=season, poster=poster, fanart=fanart,
                                  eps_watched=eps_watched, update_time=update_time, tvshowtitle=tvshowtitle, filter_lang=filter_lang,
                                  title_disable=title_disable)
            all_results += list(map(mapfunc_emp, empty_ep))

        return all_results

    def _append_episodes(self, anilist_id, episodes, eps_watched, poster, fanart, tvshowtitle, filter_lang,
                         title_disable):
        import datetime
        import time
        update_time = datetime.date.today().isoformat()
        last_updated = datetime.datetime(*(time.strptime(episodes[0]['last_updated'], "%Y-%m-%d")[0:6]))
        diff = (datetime.datetime.today() - last_updated).days

        result_ep = database.get(self.get_anilist_meta, 6, anilist_id) if diff > 0 else {}
        result_ep = [x for x in result_ep if x['type'] == 'episode']

        if len(result_ep) > len(episodes):
            season = database.get_season_list(anilist_id)['season']
            mapfunc2 = partial(self._parse_episode_view, anilist_id=anilist_id, season=season, poster=poster, fanart=fanart,
                               eps_watched=eps_watched, update_time=update_time, tvshowtitle=tvshowtitle,
                               filter_lang=filter_lang, title_disable=title_disable)
            all_results = list(map(mapfunc2, result_ep))
        else:
            mapfunc1 = partial(self._parse_episodes, eps_watched=eps_watched, title_disable=title_disable)
            all_results = list(map(mapfunc1, episodes))

        return all_results

    @staticmethod
    def _parse_episodes(res, eps_watched, title_disable):
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

    def get_episodes(self, anilist_id, filter_lang):
        kodi_meta = pickle.loads(database.get_show(anilist_id)['kodi_meta'])
        show_meta = database.get_show_meta(anilist_id)

        if show_meta:
            kodi_meta.update(pickle.loads(show_meta.get('art')))

        fanart = kodi_meta.get('fanart')
        poster = kodi_meta.get('poster')
        tvshowtitle = kodi_meta['title_userPreferred']
        eps_watched = kodi_meta.get('eps_watched')
        episodes = database.get_episode_list(anilist_id)

        title_disable = control.getSetting('general.spoilers') == 'true'
        if episodes:
            if kodi_meta['status'] != "FINISHED":
                return self._append_episodes(anilist_id, episodes, eps_watched, poster, fanart, tvshowtitle,
                                             filter_lang, title_disable), 'episodes'
            return self._process_episodes(episodes, eps_watched, title_disable), 'episodes'

        return self._process_episode_view(anilist_id, poster, fanart, eps_watched, tvshowtitle, filter_lang,
                                          title_disable), 'episodes'

    def get_anime_info(self, anilist_id):
        show = database.get_show(anilist_id)
        simkl_id = show['simkl_id']
        if not simkl_id:
            simkl_id = self.get_simkl_id('anilist', anilist_id)
            database.add_mapping_id(anilist_id, 'simkl_id', simkl_id)
        params = {
            'extended': 'full',
            'client_id': self.ClientID
        }
        r = client.request(self.baseUrl + "anime/" + str(simkl_id), params=params)
        res = json.loads(r)
        return res

    def get_anilist_meta(self, anilist_id):
        show_ids = database.get_show(anilist_id)
        simkl_id = show_ids['simkl_id']
        if not simkl_id:
            mal_id = show_ids['mal_id']
            simkl_id = self.get_simkl_id('mal', mal_id)
            database.add_mapping_id(anilist_id, 'simkl_id', simkl_id)
        params = {
            'extended': 'full',
        }
        r = client.request(self.baseUrl + "anime/episodes/" + str(simkl_id), params=params)
        res = json.loads(r)
        return res

    def get_simkl_id(self, send_id, anime_id):
        params = {
            send_id: anime_id,
            "client_id": self.ClientID,
        }
        r = client.request('{0}search/id'.format(self.baseUrl), params=params)
        r = json.loads(r)
        anime_id = r[0]['ids']['simkl']
        return anime_id

    def get_mapping_ids(self, send_id, anime_id):
        simkl_id = self.get_simkl_id(send_id, anime_id)
        params = {
            'extended': 'full',
            'client_id': self.ClientID
        }
        r = client.request('{0}/anime/{1}'.format(self.baseUrl, simkl_id), params=params)
        if r:
            r = json.loads(r)
            return r['ids']
