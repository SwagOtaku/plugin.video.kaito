# -*- coding: utf-8 -*-
from __future__ import absolute_import
from builtins import str
from builtins import map
import itertools
import json
import ast
from ..ui import database
from .WatchlistFlavorBase import WatchlistFlavorBase

class AniListWLF(WatchlistFlavorBase):
    _URL = "https://graphql.anilist.co"
    _TITLE = "AniList"
    _NAME = "anilist"
    _IMAGE = "https://anilist.co/img/icons/logo_full.png"

    #Not login, but retrieveing userId for watchlist
    def login(self):
        query = '''
        query ($name: String) {
            User(name: $name) {
                id
                }
            }
        '''

        variables = {
            "name": self._username
            }

        result = self._post_request(self._URL, json={'query': query, 'variables': variables})
        results = result.json()

        if "errors" in results:
            return

        userId = results['data']['User']['id']

        login_data = {
            'userid': str(userId)
            }

        return login_data

    def watchlist(self):
        return self._process_watchlist_view("watchlist/%d", page=1)

    def _base_watchlist_view(self, res):
        base = {
            "name": res[0],
            "url": 'watchlist_status_type/%s/%s' % (self._NAME, res[1]),
            "image": '',
            "plot": '',
        }

        return self._parse_view(base)

    def _process_watchlist_view(self, base_plugin_url, page):
        all_results = list(map(self._base_watchlist_view, self.__anilist_statuses()))
        all_results = list(itertools.chain(*all_results))
        return all_results

    def __anilist_statuses(self):
        statuses = [
            ("Next Up", "CURRENT?next_up=true"),
            ("Current", "CURRENT"),
            ("Rewatching", "REPEATING"),
            ("Plan to Watch", "PLANNING"),
            ("Paused", "PAUSED"),
            ("Completed", "COMPLETED"),
            ("Dropped", "DROPPED"),
            ]

        return statuses

    def get_watchlist_status(self, status, next_up):
        query = '''
        query ($userId: Int, $userName: String, $status: MediaListStatus, $type: MediaType, $sort: [MediaListSort]) {
            MediaListCollection(userId: $userId, userName: $userName, status: $status, type: $type, sort: $sort) {
                lists {
                    entries {
                        ...mediaListEntry
                        }
                    }
                }
            }

        fragment mediaListEntry on MediaList {
            id
            mediaId
            status
            progress
            customLists
            media {
                id
                idMal
                title {
                    userPreferred,
                    romaji,
                    english
                }
                coverImage {
                    extraLarge
                }
                startDate {
                    year,
                    month,
                    day
                }
                nextAiringEpisode {
                    episode,
                    airingAt
                }
                description
                synonyms
                format
                status
                episodes
                genres
                duration
            }
        }
        '''

        variables = {
            'userId': int(self._user_id),
            'username': self._username,
            'status': status,
            'type': 'ANIME',
            'sort': [self.__get_sort()]
            }

        return self._process_status_view(query, variables, next_up, "watchlist/%d", page=1)

    def get_watchlist_anime_entry(self, anilist_id):
        query = '''
        query ($mediaId: Int) {
            Media (id: $mediaId) {
                id
                mediaListEntry {
                    id
                    mediaId
                    status
                    score
                    progress
                    user {
                        id
                        name
                    }
                }
            }
        }
        '''

        variables = {
            'mediaId': anilist_id
            }

        result = self._post_request(self._URL, headers=self.__headers(), json={'query': query, 'variables': variables})
        results = result.json()['data']['Media']['mediaListEntry']

        anime_entry = {}
        anime_entry['eps_watched'] = results['progress']
        anime_entry['status'] = results['status'].title()
        anime_entry['score'] = results['score']

        return anime_entry

    def _process_status_view(self, query, variables, next_up, base_plugin_url, page):
        result = self._post_request(self._URL, json={'query': query, 'variables': variables})
        results = result.json()

        if "errors" in results:
            return

        try:
            entries = results['data']['MediaListCollection']['lists'][0]['entries']
        except IndexError:
            entries = []

        if next_up:
            all_results = list(map(self._base_next_up_view, reversed(entries)))
        else:
            all_results = list(map(self._base_watchlist_status_view, reversed(entries)))

        all_results = [i for i in all_results if i is not None]

        all_results = list(itertools.chain(*all_results))
        return all_results

    def _base_watchlist_status_view(self, res):
        progress = res['progress']
        res = res['media']

        #remove cached eps for releasing shows every five days so new eps metadata can be shown
        if res.get('status') == 'RELEASING':
            try:
                from datetime import datetime, timedelta
                check_update = (datetime.today() - timedelta(days=5)).strftime('%Y-%m-%d')
                last_updated = database.get_episode_list(116006)[0]['last_updated']
                if check_update == last_updated:
                    database.remove_episodes(res['id'])
            except:
                pass

##        kodi_meta = self._get_kodi_meta(res['id'], 'anilist')

        info = {}

        try:
            info['genre'] = res.get('genres')
        except:
            pass

        try:
            info['plot'] = res['description']
        except:
            pass

        try:
            info['title'] = res['title']['userPreferred']
        except:
            pass

        try:
            info['duration'] = res.get('duration') * 60
        except:
            pass

        try:
            start_date = res.get('startDate')
            info['aired'] = '{}-{:02}-{:02}'.format(start_date['year'], start_date['month'], start_date['day'])
        except:
            pass

        try:
            info['status'] = res.get('status')
        except:
            pass

        info['mediatype'] = 'tvshow'

        base = {
            "name": '%s - %d/%d' % (res["title"]["userPreferred"], progress, res['episodes'] if res['episodes'] is not None else 0),
            "url": "watchlist_query/%s/%s/%d" % (res['id'], res.get('idMal'), progress),
            "image": res['coverImage']['extraLarge'],
            "plot": info,
        }

        if res['format'] == 'MOVIE' and res['episodes'] == 1:
            base['url'] = "watchlist_to_movie/?anilist_id=%s" % (res['id'])
            base['plot']['mediatype'] = 'movie'
            return self._parse_view(base, False)

        return self._parse_view(base)

    def _base_next_up_view(self, res):
        progress = res['progress']
        res = res['media']
        next_up = progress + 1
        episode_count = res['episodes'] if res['episodes'] is not None else 0
        title = '%s - %s/%s' % (res['title']['userPreferred'], next_up, episode_count)
        poster = image = res['coverImage']['extraLarge']
        plot = None

        if episode_count > 0 and next_up > episode_count:
            return None

        if res['nextAiringEpisode'] is not None and next_up == res['nextAiringEpisode']['episode']:
            return None

        anilist_id, next_up_meta = self._get_next_up_meta('', progress, res['id'])
        if next_up_meta:
            url = 'play/%d/%d/' % (anilist_id, next_up)
            title = '%d/%d - %s' % (next_up, episode_count, next_up_meta.get('title', 'Episode {}'.format(next_up)))
            image = next_up_meta.get('image', poster)
            plot = next_up_meta.get('plot')

        info = {}

        try:
            info['genre'] = res.get('genres')
        except:
            pass

        info['episode'] = next_up

        info['title'] = title

        info['tvshowtitle'] = res['title']['userPreferred']

        info['plot'] = plot

        info['mediatype'] = 'episode'

        base = {
            "name": title,
            "url": "watchlist_query/%s/%s/%d" % (res['id'], res.get('idMal'), progress),
            "image": image,
            "plot": info,
            "fanart": image,
            "poster": poster,
        }

        if next_up_meta:
            base['url'] = url
            return self._parse_view(base, False, True)

        if res['format'] == 'MOVIE' and res['episodes'] == 1:
            base['url'] = "watchlist_to_movie/?anilist_id=%s" % (res['id'])
            base['plot']['mediatype'] = 'movie'
            return self._parse_view(base, False, True)

        return self._parse_view(base)

    def _get_titles(self, res):
        titles = list(set(res['title'].values())) + res.get('synonyms', [])[:2]
        if res['format'] == 'MOVIE':
            titles = list(res['title'].values())
        titles = '|'.join(titles[:3])
        return titles

    def __get_sort(self):
        sort_types = {
            "Score": "SCORE",
            "Progress": "PROGRESS",
            "Last Updated": "UPDATED_TIME",
            "Last Added": "ADDED_TIME",
            }

        return sort_types[self._sort]

    def __headers(self):
        headers = {
            'Authorization': 'Bearer ' + self._token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            }

        return headers

    def _kitsu_to_anilist_id(self, kitsu_id):
        arm_resp = self._get_request("https://arm.now.sh/api/v1/search?type=kitsu&id=" + kitsu_id)
        if arm_resp.status_code != 200:
            raise Exception("AnimeID not found")

        anilist_id = arm_resp.json()["services"]["anilist"]
        return anilist_id

    def watchlist_update(self, anilist_id, episode):
        return lambda: self.__update_library(episode, anilist_id)

    def __update_library(self, episode, anilist_id):
        query = '''
        mutation ($mediaId: Int, $progress : Int, $status: MediaListStatus) {
            SaveMediaListEntry (mediaId: $mediaId, progress: $progress, status: $status) {
                id
                progress
                status
                }
            }
        '''

        variables = {
            'mediaId': int(anilist_id),
            'progress': int(episode),
            'status': 'CURRENT'
            }

        self._post_request(self._URL, headers=self.__headers(), json={'query': query, 'variables': variables})
