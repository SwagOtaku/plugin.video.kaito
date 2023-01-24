import itertools
import json
import re
import time

from resources.lib.ui import control
from resources.lib.WatchlistFlavor.WatchlistFlavorBase import \
    WatchlistFlavorBase


class MyAnimeListWLF(WatchlistFlavorBase):
    _URL = "https://api.myanimelist.net/v2"
    _TITLE = "MyAnimeList"
    _NAME = "mal"
    _IMAGE = "myanimelist.png"

    def login(self):
        try:
            from six.moves import urllib_parse
            parsed = urllib_parse.urlparse(self._auth_var)
            params = dict(urllib_parse.parse_qsl(parsed.query))
            code = params['code']
            code_verifier = params['state']
        except:
            return

        oauth_url = 'https://myanimelist.net/v1/oauth2/token'
        data = {
            'client_id': 'a8d85a4106b259b8c9470011ce2f76bc',
            'code': code,
            'code_verifier': code_verifier,
            'grant_type': 'authorization_code'
        }
        res = self._get_request(oauth_url, data=data)
        res = json.loads(res)

        self._token = res['access_token']
        user = self._get_request('https://api.myanimelist.net/v2/users/@me?fields=name', headers=self.__headers())
        user = json.loads(user)

        login_data = {
            'token': res['access_token'],
            'refresh': res['refresh_token'],
            'expiry': str(time.time() + int(res['expires_in'])),
            'username': user['name']
        }

        return login_data

    def refresh_token(self, control):
        oauth_url = 'https://myanimelist.net/v1/oauth2/token'
        data = {
            'client_id': 'a8d85a4106b259b8c9470011ce2f76bc',
            'grant_type': 'refresh_token',
            'refresh_token': control.getSetting('mal.refresh')
        }
        res = self._get_request(oauth_url, data=data)
        res = json.loads(res)
        control.setSetting('mal.token', res['access_token'])
        control.setSetting('mal.refresh', res['refresh_token'])
        control.setSetting('mal.expiry', str(time.time() + int(res['expires_in'])))

    def _handle_paging(self, hasNextPage, base_url, page):
        if not hasNextPage:
            return []

        next_page = page + 1
        name = "Next Page (%d)" % (next_page)
        offset = (re.compile("offset=(.+?)&").findall(hasNextPage))[0]
        return self._parse_view({'name': name, 'url': base_url % (offset, next_page), 'image': 'next.png', 'plot': None, 'fanart': 'next.png'})

    def watchlist(self):
        return self._process_watchlist_view('', "watchlist_page/%d", page=1)

    def _base_watchlist_view(self, res):
        base = {
            "name": res[0],
            "url": 'watchlist_status_type/%s/%s' % (self._NAME, res[1]),
            "image": res[0].lower() + '.png',
            "plot": '',
        }

        return self._parse_view(base)

    def _process_watchlist_view(self, params, base_plugin_url, page):
        all_results = list(map(self._base_watchlist_view, self.__mal_statuses()))
        all_results = list(itertools.chain(*all_results))
        return all_results

    def __mal_statuses(self):
        statuses = [
            ("Next Up", "watching?next_up=true"),
            ("Currently Watching", "watching"),
            ("Completed", "completed"),
            ("On Hold", "on_hold"),
            ("Dropped", "dropped"),
            ("Plan to Watch", "plan_to_watch"),
            ("All Anime", ""),
        ]

        return statuses

    def get_watchlist_status(self, status, next_up, offset=0, page=1):
        fields = [
            'alternative_titles',
            'list_status',
            'num_episodes',
            'synopsis',
            'mean',
            'rating',
            'genres',
            'studios',
            'start_date',
            'average_episode_duration',
            'media_type',
            'status',
            'videos'
        ]
        params = {
            "status": status,
            "sort": self.__get_sort(),
            "limit": 100,
            "offset": offset,
            "fields": ','.join(fields),
        }

        url = self._to_url("users/@me/animelist")
        return self._process_status_view(url, params, next_up, "watchlist_status_type_pages/mal/%s/%%s/%%d" % status, page)

    def get_watchlist_anime_entry(self, anilist_id):
        mal_id = self._get_mapping_id(anilist_id, 'mal_id')

        if not mal_id:
            return

        params = {
            "fields": 'my_list_status',
        }

        url = self._to_url("users/@me/animelist")
        results = self._get_request(url, headers=self.__headers(), params=params)
        results = json.loads(results)['data'][0]['node']['my_list_status']

        anime_entry = {}
        anime_entry['eps_watched'] = results['num_episodes_watched']
        anime_entry['status'] = results['status'].title()
        anime_entry['score'] = results['score']

        return anime_entry

    def _process_status_view(self, url, params, next_up, base_plugin_url, page):
        results = self._get_request(url, headers=self.__headers(), params=params)
        results = json.loads(results)

        if next_up:
            all_results = list(map(self._base_next_up_view, results['data']))
        else:
            all_results = list(map(self._base_watchlist_status_view, results['data']))

        all_results = list(itertools.chain(*all_results))

        all_results += self._handle_paging(results['paging'].get('next'), base_plugin_url, page)
        return all_results

    def _base_watchlist_status_view(self, res):
        info = {}

        try:
            info['plot'] = res['node']['synopsis']
        except:
            pass

        title = res['node'].get('title')
        if self._title_lang == 'english':
            title = res['node'].get('alternative_titles').get('en') or title
        info['title'] = title

        try:
            info['duration'] = res['node']['average_episode_duration']
        except:
            pass

        try:
            info['genre'] = [x.get('name') for x in res['node']['genres']]
        except:
            pass

        try:
            info['status'] = res['node']['status']
        except:
            pass

        try:
            start_date = res['node']['start_date']
            info['premiered'] = start_date
            info['year'] = start_date[:4]
        except:
            pass

        try:
            info['studio'] = [x.get('name') for x in res['node']['studios']]
        except:
            pass

        try:
            info['rating'] = res['node']['mean']
        except:
            pass

        try:
            info['mpaa'] = res['node']['rating']
        except:
            pass

        info['mediatype'] = 'tvshow'

        base = {
            "name": '%s - %s/%s' % (title, res['list_status']["num_episodes_watched"], res['node']["num_episodes"]),
            "url": "watchlist_to_ep/%s/%s" % (res['node']['id'], res['list_status']["num_episodes_watched"]),
            "image": res['node']['main_picture'].get('large', res['node']['main_picture']['medium']),
            "plot": info,
        }

        if res['node']['media_type'] == 'movie' and res['node']["num_episodes"] == 1:
            base['url'] = "watchlist_to_movie/%s" % (res['node']['id'])
            base['plot']['mediatype'] = 'movie'
            return self._parse_view(base, False)

        return self._parse_view(base)

    def _base_next_up_view(self, res):
        mal_id = res['node']['id']
        progress = res['list_status']["num_episodes_watched"]
        next_up = progress + 1
        episode_count = res['node']["num_episodes"]
        base_title = res['node'].get('title')
        if self._title_lang == 'english':
            base_title = res['node'].get('alternative_titles').get('en') or base_title
        title = '%s - %s/%s' % (base_title, next_up, episode_count)
        poster = image = res['node']['main_picture'].get('large', res['node']['main_picture']['medium'])
        plot = aired = None

        anilist_id, next_up_meta = self._get_next_up_meta(mal_id, int(progress))
        if next_up_meta:
            url = 'play/%d/%d/' % (anilist_id, next_up)
            if next_up_meta.get('title'):
                title = '%s - %s' % (title, next_up_meta.get('title'))
            if next_up_meta.get('image'):
                image = next_up_meta.get('image')
            plot = next_up_meta.get('plot')
            aired = next_up_meta.get('aired')

        info = {}

        info['episode'] = next_up
        info['title'] = title
        info['tvshowtitle'] = res['node']['title']
        info['duration'] = res['node']['average_episode_duration']
        info['plot'] = plot
        info['mediatype'] = 'episode'
        info['aired'] = aired
        

        base = {
            "name": title,
            "url": "watchlist_to_ep/%s//%s" % (res['node']['id'], res['list_status']["num_episodes_watched"]),
            "image": image,
            "plot": info,
            "fanart": image,
            "poster": poster,
        }

        if next_up_meta:
            base['url'] = url
            return self._parse_view(base, False)

        if res['node']['media_type'] == 'movie' and res['node']["num_episodes"] == 1:
            base['url'] = "watchlist_to_movie/%s" % (res['node']['id'])
            base['plot']['mediatype'] = 'movie'
            return self._parse_view(base, False)

        return self._parse_view(base)

    def __headers(self):
        header = {
            'Authorization': "Bearer {}".format(self._token),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        return header

    def _kitsu_to_mal_id(self, kitsu_id):
        arm_resp = self._get_request("https://arm.now.sh/api/v1/search?type=kitsu&id=" + kitsu_id)
        if not arm_resp:
            raise Exception("AnimeID not found")

        mal_id = json.loads(arm_resp)["services"]["mal"]
        return mal_id

    def watchlist_update(self, anilist_id, episode):
        mal_id = self._get_mapping_id(anilist_id, 'mal_id')

        if not mal_id:
            return

        url = self._to_url("anime/%s/my_list_status" % (mal_id))
        data = {
            'num_watched_episodes': int(episode)
        }

        return lambda: self.__update_watchlist(anilist_id, episode, url, data)

    def __update_watchlist(self, anilist_id, episode, url, data):
        _ = self._put_request(url, data=data, headers=self.__headers())

    def __get_sort(self):
        sort_types = {
            "Anime Title": "anime_title",
            "Last Updated": "list_updated_at",
            "Anime Start Date": "anime_start_date",
            "List Score": "list_score"
        }

        return sort_types[self._sort]

    def watchlist_append(self, anilist_id):
        mal_id = self._get_mapping_id(anilist_id, 'mal_id')
        if not mal_id:
            return
        url = self._to_url("anime/%s/my_list_status" % (mal_id))
        data = {'status': 'plan_to_watch'}
        result = json.loads(self._put_request(url, data=data, headers=self.__headers()))
        if result.get('status'):
            control.notify('Added to Watchlist')
        return

    def watchlist_remove(self, mal_id):
        url = self._to_url("anime/%s/my_list_status" % (mal_id))
        _ = self._delete_request(url, headers=self.__headers())
        control.notify('Removed from Watchlist')
        return
