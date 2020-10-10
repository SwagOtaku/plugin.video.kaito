import json
from ui import utils, database
from debrid import real_debrid
import pages
from ui.BrowserBase import BrowserBase
from indexers import simkl, trakt
import ast
import requests
import datetime

class KaitoBrowser(BrowserBase):

    def _parse_history_view(self, res):
        name = res
        return utils.allocate_item(name, "search/" + name + "/1", True)

    def _json_request(self, url, data=''):
        response = json.loads(self._get_request(url, data))
        return response

    # TODO: Not sure i want this here..
    def search_history(self,search_array):
    	result = map(self._parse_history_view,search_array)
    	result.insert(0,utils.allocate_item("New Search", "search", True))
    	result.insert(len(result),utils.allocate_item("Clear Search History...", "clear_history", True))
    	return result

    def get_latest(self, real_debrid_enabled):
        if real_debrid_enabled:
            page = pages.nyaa.sources
        else:
            page = pages.gogoanime.sources

        latest = database.get(page().get_latest, 0.125)
        return latest

    def get_latest_dub(self, real_debrid_enabled):
        if real_debrid_enabled:
            page = pages.nyaa.sources
        else:
            page = pages.gogoanime.sources

        latest_dub = database.get(page().get_latest_dub, 0.125)
        return latest_dub

    def get_backup(self, anilist_id, source):
        show = database.get_show(anilist_id)
        mal_id = show['mal_id']

        if not mal_id:
            mal_id = self.get_mal_id(anilist_id)
            database.add_mapping_id(anilist_id, 'mal_id', str(mal_id))

        result = requests.get("https://kaito-b.firebaseio.com/%s/Sites/%s.json" % (mal_id, source))
        return result.json()

    def get_mal_id(self, anilist_id):
        arm_resp = self._json_request("https://armkai.vercel.app/api/search?type=anilist&id={}".format(anilist_id))
        mal_id = arm_resp["mal"]
        return mal_id

    def clean_show(self, show_id, meta_ids):
        database.add_meta_ids(show_id, meta_ids)
        database.remove_season(show_id)
        database.remove_episodes(show_id)
        name = ast.literal_eval(database.get_show(show_id)['kodi_meta'])
        name.pop('fanart', None)
        database.add_fanart(show_id, name)

    def search_trakt_shows(self, anilist_id):
        shows = trakt.TRAKTAPI().search_trakt_shows(anilist_id)
        return shows

    def get_trakt_episodes(self, show_id, season, page=1):
        return trakt.TRAKTAPI().get_trakt_episodes(show_id, season)

    def get_anime_trakt(self, anilist_id):
        anime = trakt.TRAKTAPI().get_anime(anilist_id)

        if not anime:
            anime = self.get_anime_simkl(anilist_id)

        return anime

    def get_anime_simkl(self, anilist_id):
        return simkl.SIMKLAPI().get_anime(anilist_id)

    def get_anime_init(self, anilist_id):
        show_meta = database.get_show(anilist_id)

        if not show_meta:
            from AniListBrowser import AniListBrowser
            show_meta = AniListBrowser().get_anilist(anilist_id)

        if not show_meta['meta_ids']:
            name = ast.literal_eval(show_meta['kodi_meta'])['name']
            trakt_id = trakt.TRAKTAPI().get_trakt_id(name)

            if not trakt_id:
                return self.get_anime_simkl(anilist_id)

            database.add_meta_ids(anilist_id, str(trakt_id))

        return self.get_anime_trakt(anilist_id)

    def get_episodeList(self, show_id, pass_idx):
        from ui import control

        episodes = database.get_episode_list(int(show_id))

        if episodes:
            items = trakt.TRAKTAPI()._process_trakt_episodes(show_id, '', episodes, '')
        else:
            items = simkl.SIMKLAPI().get_episodes(show_id)

        items =  [i for i in items if self.is_aired(i['info'])]

        playlist = control.bulk_draw_items(items)[pass_idx:]

        for i in playlist:
            url = i[0]
            control.playList.add(url=url, listitem=i[1])

    def is_aired(self, info):
        try:
            try:
                air_date = info['aired']               
            except:
                air_date = info.get('premiered')
            if not air_date:
                return False
            if int(air_date[:4]) < 2019:
                return True

            todays_date = datetime.datetime.today().strftime('%Y-%m-%d')

            if air_date > todays_date:
                return False
            else:
                return True
        except:
            import traceback
            traceback.print_exc()
            # Assume an item is not aired if we do not have any information on it or fail to identify
            return False

    def get_sources(self, anilist_id, episode, media_type):
        show = database.get_show(anilist_id)
        query = ast.literal_eval(show['kodi_meta'])['query']
        actionArgs = {
            'query': query,
            'anilist_id': anilist_id,
            'episode': episode,
            'media_type': media_type,
            'get_backup': self.get_backup
            }
        sources = pages.getSourcesHelper(actionArgs)
        return sources

    def get_latest_sources(self, hash_):
        magnet = 'magnet:?xt=urn:btih:' + hash_
        api = real_debrid.RealDebrid()
        link = api.resolve_single_magnet(hash_, magnet)
        return link
