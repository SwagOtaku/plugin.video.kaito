import requests
import json
import ast
from functools import partial
from tmdb import TMDBAPI
from ..ui import database, utils

class SIMKLAPI:
    def __init__(self):
        self.ClientID = "5178a709b7942f1f5077b737b752eea0f6dee684d0e044fa5acee8822a0cbe9b"
        self.baseUrl = "https://api.simkl.com/"
        self.imagePath = "https://simkl.net/episodes/%s_w.jpg"
        self.art = {}
        self.request_response = None
        self.threads = []

    def _to_url(self, url=''):
        if url.startswith("/"):
            url = url[1:]

        return "%s/%s" % (self.baseUrl, url)

    def _json_request(self, url, data=''):
        response = requests.get(url, data)
        response = response.json()
        return response

    def _parse_episode_view(self, res, anilist_id, poster, fanart, eps_watched):
        url = "%s/%s" % (anilist_id, res['episode'])
        name = 'Ep. %d (%s)' % (res['episode'], res.get('title'))
        image =  self.imagePath % res['img']
        info = {}
        info['plot'] = res['description']
        info['title'] = res['title']
        info['season'] = 1
        info['episode'] = res['episode']
        try:
            if int(eps_watched) >= res['episode']:
                info['playcount'] = 1
        except:
            pass
        try:
            info['aired'] = res['date'][:10]
        except:
            pass
        info['tvshowtitle'] = ast.literal_eval(database.get_show(anilist_id)['kodi_meta'])['name']
        info['mediatype'] = 'episode'
        parsed = utils.allocate_item(name, "play/" + str(url), False, image, info, fanart, poster)
        return parsed

    def _process_episode_view(self, anilist_id, json_resp, base_plugin_url, page):
        kodi_meta = ast.literal_eval(database.get_show(anilist_id)['kodi_meta'])
        fanart = kodi_meta.get('fanart')
        poster = kodi_meta.get('poster')
        eps_watched = kodi_meta.get('eps_watched')
        json_resp = filter(lambda x: x['type'] == 'episode', json_resp)
        mapfunc = partial(self._parse_episode_view, anilist_id=anilist_id, poster=poster, fanart=fanart, eps_watched=eps_watched)
        all_results = map(mapfunc, json_resp)

        return all_results

    def get_anime(self, anilist_id):
        show = database.get_show(anilist_id)

        if show['simkl_id']:
            return self.get_episodes(anilist_id), 'episodes'

        show_meta = show['meta_ids']
        kodi_meta = ast.literal_eval(show['kodi_meta'])
        mal_id = show['mal_id']

        if not mal_id:
            mal_id = self.get_mal_id(anilist_id)
            database.add_mapping_id(anilist_id, 'mal_id', str(mal_id))

        simkl_id = str(self.get_anime_id(mal_id))
        database.add_mapping_id(anilist_id, 'simkl_id', simkl_id)
        if show_meta:
            show_meta = ast.literal_eval(show['meta_ids'])
            if not kodi_meta.get('fanart'):
                kodi_meta['fanart'] = TMDBAPI().showFanart(show_meta).get('fanart')
                database.update_kodi_meta(int(anilist_id), kodi_meta)


        return self.get_episodes(anilist_id), 'episodes'

    def _get_episodes(self, anilist_id):
        simkl_id = database.get_show(anilist_id)['simkl_id']
        data = {
            "extended": 'full',
        }
        url = self._to_url("anime/episodes/%s" % str(simkl_id))
        json_resp = self._json_request(url, data)
        return json_resp

    def get_episodes(self, anilist_id, page=1):
        episodes = database.get(self._get_episodes, 6, anilist_id)
        return self._process_episode_view(anilist_id, episodes, "animes_page/%s/%%d" % anilist_id, page)

    def get_anime_search(self, q):
        data = {
            "q": q,
            "client_id": self.ClientID
        }
        json_resp = self._json_request("https://api.simkl.com/search/anime", data)
        if not json_resp:
            return []

        anime_id = json_resp[0]['ids']['simkl_id']
        return anime_id

    def get_anime_id(self, mal_id):
        data = {
            "mal": mal_id,
            "client_id": self.ClientID,
        }
        url = self._to_url("search/id")
        json_resp = self._json_request(url, data)
        if not json_resp:
            return []

        anime_id = json_resp[0]['ids'].get('simkl')
        return anime_id

    def get_mal_id(self, anilist_id):
        arm_resp = self._json_request("https://arm2.vercel.app/api/search?type=anilist&id={}".format(anilist_id))
        mal_id = arm_resp["mal"]
        return mal_id
