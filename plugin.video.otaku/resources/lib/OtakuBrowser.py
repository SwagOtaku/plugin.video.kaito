import json
import pickle

from resources.lib import pages
from resources.lib.indexers import simkl, consumet, enime
from resources.lib.ui import client, control, database, utils
from resources.lib.ui.BrowserBase import BrowserBase
from resources.lib.AniListBrowser import AniListBrowser


class OtakuBrowser(BrowserBase):

    @staticmethod
    def _parse_history_view(res):
        name = res
        return utils.allocate_item(name, "search/%s/1" % name, True)

    def search_history(self, search_array):
        result = list(map(self._parse_history_view, search_array))
        result.insert(0, utils.allocate_item("New Search", "search", True, 'new_search.png'))
        result.insert(len(result), utils.allocate_item("Clear Search History...", "clear_history", True, 'clear_search_history.png'))
        return result

    @staticmethod
    def _parse_history_view_movie(res):
        name = res
        return utils.allocate_item(name, "search_movie/%s/1" % name, True)

    def search_history_movie(self, search_array):
        result = list(map(self._parse_history_view_movie, search_array))
        result.insert(0, utils.allocate_item("New Search", "search_movie", True, 'new_search.png'))
        result.insert(len(result), utils.allocate_item("Clear Search History...", "clear_history_movie", True, 'clear_search_history.png'))
        return result

    @staticmethod
    def _parse_history_view_tv(res):
        name = res
        return utils.allocate_item(name, "search_tv/%s/1" % name, True)

    def search_history_tv(self, search_array):
        result = list(map(self._parse_history_view_tv, search_array))
        result.insert(0, utils.allocate_item("New Search", "search_tv", True, 'new_search.png'))
        result.insert(len(result), utils.allocate_item("Clear Search History...", "clear_history_tv", True, 'clear_search_history.png'))
        return result

    def get_backup(self, anilist_id, source):
        show = database.get_show(anilist_id)
        mal_id = show['mal_id']

        if not mal_id:
            mal_id = self.get_mal_id(anilist_id)
            database.add_mapping_id(anilist_id, 'mal_id', str(mal_id))

        result = client.request("https://arm2.vercel.app/api/kaito-b?type=myanimelist&id={}".format(mal_id))
        if result:
            result = json.loads(result)
            result = result.get('Pages', {}).get(source, {})
        return result

    @staticmethod
    def get_mal_id(anilist_id):
        arm_resp = client.request("https://armkai.vercel.app/api/search?type=anilist&id={}".format(anilist_id))
        arm_resp = json.loads(arm_resp)
        mal_id = arm_resp["mal"]
        return mal_id

    def get_anime_init(self, anilist_id, filter_lang=None):
        show = database.get_show(anilist_id)
        if not show:
            from resources.lib.AniListBrowser import AniListBrowser
            show = AniListBrowser().get_anilist(anilist_id)

        # show_meta = database.get_show_meta(anilist_id)
        # if not show_meta:
        #     kodi_meta = pickle.loads(show['kodi_meta'])
        #     name = kodi_meta['ename'] or kodi_meta['name']
        #     mtype = 'movie' if kodi_meta.get('format') == 'MOVIE' else 'tv'
        #     trakt_id = trakt.TRAKTAPI().get_trakt_id(name, mtype=mtype)
        #     if trakt_id:
        #         database.add_meta_ids(anilist_id, trakt_id)
        # else:
        #     trakt_id = pickle.loads(show_meta.get('meta_ids'))

        # kodi_meta = pickle.loads(show.get('kodi_meta'))
        # title = kodi_meta.get('ename') or kodi_meta.get('name')
        # p = re.search(r'(?:part|cour)\s*\d', title, re.I)
        # if not trakt_id or p:
        # if not trakt_id:

        # if control.getSetting("override.episode.bool") == 'true':
        #     selected_api = control.getSetting("override.episode.menu")
        #     if selected_api == "Consumet":
        #         data = consumet.CONSUMETAPI().get_episodes(anilist_id, filter_lang)
        #     elif selected_api == "Simkl":
        #         data = simkl.SIMKLAPI().get_episodes(anilist_id, filter_lang)
        #     else:
        #         data = ([], 'episodes')
        # else:
        data = simkl.SIMKLAPI().get_episodes(anilist_id, filter_lang)
        if not data[0]:
            data = consumet.CONSUMETAPI().get_episodes(anilist_id, filter_lang)
        return data

    @staticmethod
    def get_episodeList(anilist_id, pass_idx, filter_lang=None):
        show = database.get_show(anilist_id)
        kodi_meta = pickle.loads(show['kodi_meta'])
        if kodi_meta['format'] == 'MOVIE' and kodi_meta['episodes'] == 1:
            title = kodi_meta.get('userPreferred') or kodi_meta['name']
            info = {
                "title": title,
                "mediatype": 'movie',
                'plot': kodi_meta['plot'],
                'rating': kodi_meta['rating'],
                'premiered': str(kodi_meta['start_date']),
                'year': int(str(kodi_meta['start_date'])[:4])
            }
            items = [utils.allocate_item(title, 'null', info=info, poster=kodi_meta['poster'])]

        else:
            episodes = database.get_episode_list(anilist_id)
            items = enime.ENIMEAPI()._process_episodes(episodes, '') if episodes else []
            playlist = control.bulk_draw_items(items)[pass_idx:]
            if len(playlist) > int(control.getSetting('general.playlist_length')):
                playlist = playlist[:int(control.getSetting('general.playlist_length'))]

            for i in playlist:
                url = i[0]
                if filter_lang:
                    url += filter_lang
                control.playList.add(url=url, listitem=i[1])
        return items

    def get_sources(self, anilist_id, episode, filter_lang, media_type, rescrape=False, source_select=False):
        show = database.get_show(anilist_id)
        if not show:
            show = AniListBrowser().get_anilist(anilist_id)
        kodi_meta = pickle.loads(show['kodi_meta'])
        actionArgs = {
            'query': kodi_meta['query'],
            'anilist_id': anilist_id,
            'episode': episode,
            'status': kodi_meta['status'],
            'filter_lang': filter_lang,
            'media_type': media_type,
            'rescrape': rescrape,
            'get_backup': self.get_backup,
            'source_select': source_select,
            'duration': kodi_meta.get('duration', -1)
        }
        sources = pages.getSourcesHelper(actionArgs)
        return sources
