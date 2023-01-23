import json
import pickle
import re
from functools import partial

from resources.lib.indexers.fanart import FANARTAPI
from resources.lib.indexers.tmdb import TMDBAPI
from resources.lib.ui import client, database, utils
from six.moves import urllib_parse


class TRAKTAPI:
    def __init__(self):
        self.ClientID = "94babdea045e1b9cfd54b278f7dda912ae559fde990590db9ffd611d4806838c"
        self.baseUrl = 'https://api.trakt.tv/'
        self.art = {}
        self.request_response = None
        self.headers = {'trakt-api-version': '2',
                        'trakt-api-key': self.ClientID,
                        'content-type': 'application/json'}

    def _json_request(self, url):
        url = self.baseUrl + url
        response = client.request(url, headers=self.headers)
        if response:
            response = json.loads(response)
        return response

    # def _parse_trakt_seasons(self, res, show_id, eps_watched):
    #     parsed = pickle.loads(res['kodi_meta'])

    #     try:
    #         if int(eps_watched) >= res['number']:
    #             parsed['info']['playcount'] = 1
    #     except:
    #         pass

    #     return parsed

    # def _parse_search_trakt(self, res, show_id):
    #     url = '%s/%s' % (show_id, res['show']['ids'])
    #     name = res['show']['title']
    #     image = TMDBAPI().showPoster(res['show']['ids'])
    #     if image:
    #         image = image['poster']
    #     info = {}
    #     info['plot'] = res['show']['overview']
    #     info['mediatype'] = 'tvshow'
    #     parsed = utils.allocate_item(name, "season_correction_database/" + str(url), True, image, info)
    #     return parsed

    # def _parse_trakt_view(self, res, show_id, show_meta):
    #     url = '%s/%d' % (show_id, res['number'])
    #     name = res['title']
    #     meta = TMDBAPI().showSeasonToListItem(res['number'], show_meta)
    #     if meta:
    #         image = meta.get('poster')
    #         fanart = meta.get('fanart')
    #         poster = meta.get('poster')
    #     info = {}
    #     info['plot'] = res['overview']
    #     info['mediatype'] = 'season'
    #     parsed = utils.allocate_item(name, "animes_trakt/" + str(url), True, image, info, fanart=fanart, poster=poster)
    #     return parsed

    # def _parse_trakt_episode_view(self, res, show_id, show_meta, season, poster, fanart, eps_watched, update_time):
    #     url = "%s/%s/" % (show_id, res['number'])
    #     name = 'Ep. %d (%s)' % (res['number'], res.get('title', ''))
    #     try:
    #         image = TMDBAPI().episodeIDToListItem(season, res['number'], show_meta)['thumb']
    #     except:
    #         image = 'DefaultVideo.png'
    #     info = {}
    #     info['plot'] = res['overview']
    #     info['title'] = res.get('title', '')
    #     info['season'] = int(season)
    #     info['episode'] = res['number']
    #     try:
    #         if int(eps_watched) >= res['number']:
    #             info['playcount'] = 1
    #     except:
    #         pass
    #     try:
    #         info['aired'] = res['first_aired'][:10]
    #     except:
    #         pass
    #     info['tvshowtitle'] = pickle.loads(database.get_show(show_id)['kodi_meta'])['title_userPreferred']
    #     info['mediatype'] = 'episode'
    #     parsed = utils.allocate_item(name, "play/" + str(url), False, image, info, fanart, poster)
    #     database._update_episode(show_id, season, res['number'], res['number_abs'], update_time, parsed)
    #     return parsed

    # def _process_trakt_episodes(self, anilist_id, season, episodes, eps_watched):
    #     mapfunc = partial(self._parse_trakt_seasons, show_id=anilist_id, eps_watched=eps_watched)
    #     all_results = list(map(mapfunc, episodes))

    #     return all_results

    # def _process_season_view(self, anilist_id, meta_ids, kodi_meta, url):
    #     result = self._json_request(url)
    #     mapfunc = partial(self._parse_trakt_view, show_id=anilist_id, show_meta=meta_ids)
    #     all_results = list(map(mapfunc, result))
    #     return all_results, 'seasons'

    # def _process_direct_season_view(self, anilist_id, meta_ids, kodi_meta, url):
    #     result = self._json_request(url)

    #     try:
    #         season_year = kodi_meta['start_date'].split('-')[0] + '-'
    #         seasons = [k for k in result if k['number'] != 0]
    #         season = next((item for item in seasons if season_year in item["first_aired"]), None)
    #         database._update_season(anilist_id, season['number'])
    #         all_results = self.get_trakt_episodes(anilist_id, season['number']), 'episodes'
    #     except:
    #         mapfunc = partial(self._parse_trakt_view, show_id=anilist_id, show_meta=meta_ids)
    #         all_results = list(map(mapfunc, result))

    #     return all_results, 'seasons'

    # def _process_trakt_episode_view(self, anilist_id, show_meta, season, poster, fanart, eps_watched, url, data, base_plugin_url):
    #     from datetime import date
    #     update_time = date.today().isoformat()
    #     result = self._json_request(url)
    #     mapfunc = partial(self._parse_trakt_episode_view, show_id=anilist_id, show_meta=show_meta, season=season, poster=poster, fanart=fanart, eps_watched=eps_watched, update_time=update_time)
    #     all_results = list(map(mapfunc, result))
    #     return all_results

    # def get_trakt_id(self, name, mtype='tv'):
    #     name = re.sub(r'(?i)(?:part|cour)\s\d+$', '', name)
    #     name = re.sub(r'(?i)(?:season)?\s\d+$', '', name)
    #     rtype = 'show' if mtype == 'tv' else 'movie'
    #     url = 'search/%s?query=%s&genres=anime&extended=full' % (rtype, urllib_parse.quote(name.strip()))
    #     result = database.get(self._json_request, 4, url)

    #     if not result:
    #         name = name.replace('?', '')
    #         roman = r'(X{1,3}(IX|IV|V?I{0,3})|X{0,3}(IX|I?V|V?I{1,3}))$'
    #         name = re.sub(roman, '', name)
    #         if ':' in name:
    #             name = name.split(':')[0]
    #         url = 'search/%s?query=%s&genres=anime&extended=full' % (rtype, urllib_parse.quote(name.strip()))
    #         result = database.get(self._json_request, 4, url)

    #     if not result:
    #         return

    #     return result[0][rtype]['ids']

    def get_trakt(self, name, mtype='tv', year=''):
        name = re.sub(r'(?i)(?:part|cour)\s\d+$', '', name)
        name = re.sub(r'(?i)season\s\d+$', '', name)
        name = re.sub(r'(?i)(?:ova|special)s?$', '', name)
        rtype = 'show' if mtype == 'tv' else 'movie'
        url = 'search/%s?query=%s&genres=anime&extended=full' % (rtype, urllib_parse.quote(name.strip()))
        if year:
            url += '&years=%s' % year
        result = database.get(self._json_request, 4, url)

        if not result:
            name = name.replace('?', '')
            name = re.sub(r'\s\d+$', '', name)
            roman = r'(X{1,3}(IX|IV|V?I{0,3})|X{0,3}(IX|I?V|V?I{1,3}))$'
            name = re.sub(roman, '', name)
            if ':' in name:
                name = name.split(':')[0]
            url = 'search/%s?query=%s&genres=anime&extended=full' % (rtype, urllib_parse.quote(name.strip()))
            result = database.get(self._json_request, 4, url)

        if not result:
            return

        jres = {}
        if len(result) > 1:
            for res in result:
                if res.get(rtype).get('title').lower == name.lower():
                    jres = res
                    break
        if not jres:
            jres = result[0]

        return jres.get(rtype)

    # def search_trakt_shows(self, anilist_id):
    #     kodi_meta = pickle.loads(database.get_show(anilist_id)['kodi_meta'])
    #     name = kodi_meta['ename'] or kodi_meta['name']
    #     url = 'search/show?query=%s&genres=anime&extended=full' % urllib_parse.quote(name)
    #     result = self._json_request(url)

    #     if not result:
    #         name = re.sub(r'(?i)(?:part)?\s\d+$', '', name)
    #         name = re.sub(r'(?i)(?:season)?\s\d+', '', name)
    #         name = name.replace('?', '')
    #         url = 'search/show?query=%s&genres=anime&extended=full' % urllib_parse.quote(name)
    #         result = self._json_request(url)

    #     if not result:
    #         return []

    #     mapfunc = partial(self._parse_search_trakt, show_id=anilist_id)
    #     all_results = list(map(mapfunc, result))
    #     return all_results

    # def _add_fanart(self, anilist_id, meta_ids, kodi_meta):
    #     if not kodi_meta.get('fanart'):
    #         mtype = 'tv'
    #         if kodi_meta.get('episodes') == 1 and kodi_meta.get('status') == 'FINISHED':
    #             mtype = 'movies'
    #         meta = FANARTAPI().getArt(meta_ids, mtype)
    #         if meta:
    #             kodi_meta.update(meta)
    #             database.update_kodi_meta(anilist_id, kodi_meta)
    #         else:
    #             fanart = TMDBAPI().showFanart(meta_ids)
    #             if fanart:
    #                 kodi_meta['fanart'] = fanart.get('fanart')
    #                 database.update_kodi_meta(anilist_id, kodi_meta)

    # def get_trakt_seasons(self, anilist_id, meta_ids, kodi_meta, db_correction):
    #     # _ = self._add_fanart(anilist_id, meta_ids, kodi_meta)
    #     if not meta_ids.get('trakt'):
    #         return []
    #     url = 'shows/%d/seasons?extended=full' % meta_ids.get('trakt')

    #     if db_correction:
    #         target = self._process_season_view
    #     else:
    #         target = self._process_direct_season_view

    #     return target(anilist_id, meta_ids, kodi_meta, url)

    # def get_anime(self, anilist_id, db_correction):
    #     seasons = database.get_season_list(anilist_id)

    #     if seasons:
    #         return self.get_trakt_episodes(anilist_id, seasons['season']), 'episodes'

    #     show = database.get_show(anilist_id)
    #     show_meta = database.get_show_meta(anilist_id)
    #     kodi_meta = pickle.loads(show['kodi_meta'])
    #     meta_ids = pickle.loads(show_meta['meta_ids']) if show_meta else {}

    #     if kodi_meta['episodes'] is None or int(kodi_meta['episodes']) > 30:
    #         return

    #     return self.get_trakt_seasons(anilist_id, meta_ids, kodi_meta, db_correction)

    # def get_trakt_episodes(self, show_id, season):
    #     show_meta = database.get_show_meta(show_id)
    #     meta_ids = pickle.loads(show_meta.get('meta_ids'))
    #     kodi_meta = pickle.loads(database.get_show(show_id)['kodi_meta'])
    #     kodi_meta.update(pickle.loads(show_meta.get('art')))
    #     fanart = kodi_meta.get('fanart')
    #     poster = kodi_meta.get('poster')
    #     eps_watched = kodi_meta.get('eps_watched')
    #     episodes = database.get_episode_list(int(show_id))

    #     if episodes:
    #         return self._process_trakt_episodes(show_id, season, episodes, eps_watched)

    #     url = "shows/%d/seasons/%s?extended=full" % (meta_ids['trakt'], str(season))
    #     data = ''
    #     return self._process_trakt_episode_view(show_id, meta_ids, season, poster, fanart, eps_watched, url, data, "animes_page/%s/%%d" % show_id)

    # def get_ids_by_slug(self, slug, mtype='shows'):
    #     url = '{0}/{1}'.format(mtype, slug)
    #     result = self._json_request(url)
    #     return result.get('ids')
