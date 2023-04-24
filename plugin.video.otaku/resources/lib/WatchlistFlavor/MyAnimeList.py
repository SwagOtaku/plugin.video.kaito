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
            from six.moves import urllib_parse  # Importing urllib_parse from Six's module
            parsed = urllib_parse.urlparse(self._auth_var)  # Parsing self._auth_var
            params = dict(urllib_parse.parse_qsl(parsed.query))  # Extracting parameters from parsed query and creating a dictionary
            code = params['code']  # Assigning the value of 'code' key to variable 'code'
            code_verifier = params['state']  # Assigning the value of 'state' key to variable 'code_verifier'
        except:   # Exception handler in case of error
            return   # Returns None

        oauth_url = 'https://myanimelist.net/v1/oauth2/token'   # Assigning URL to oauth_url
        data = {   # Dictionary containing necessary data for API call
            'client_id': 'a8d85a4106b259b8c9470011ce2f76bc',
            'code': code,
            'code_verifier': code_verifier,
            'grant_type': 'authorization_code'
        }
        res = self._get_request(oauth_url, data=data)   # Making a request to API with given URL and data
        res = json.loads(res)   # Converting response to JSON format

        self._token = res['access_token']   # Saving access token received from API in '_token' variable
        user = self._get_request('https://api.myanimelist.net/v2/users/@me?fields=name', headers=self.__headers())   # Making a request using access token to get user details
        user = json.loads(user)   # Converting response to JSON format

        login_data = {   # Dictionary containing user's data
            'token': res['access_token'],
            'refresh': res['refresh_token'],
            'expiry': str(time.time() + int(res['expires_in'])),
            'username': user['name']
        }

        return login_data   # Returning the dictionary 'login_data'

    def refresh_token(self):
        oauth_url = 'https://myanimelist.net/v1/oauth2/token'   # Oauth URL
        data = {  # Data required for making an API call
            'client_id': 'a8d85a4106b259b8c9470011ce2f76bc',
            'grant_type': 'refresh_token',
            'refresh_token': control.getSetting('mal.refresh')
        }
        res = self._get_request(oauth_url, data=data)   # Making a request to API with given URL and data
        res = json.loads(res)   # Converting response to JSON format
        control.setSetting('mal.token', res['access_token'])   # Setting access token in control's settings
        control.setSetting('mal.refresh', res['refresh_token'])   # Setting refresh token in control's settings
        control.setSetting('mal.expiry', str(time.time() + int(res['expires_in'])))   # Setting expiration time of token in control's settings

    def _handle_paging(self, hasNextPage, base_url, page):
        if not hasNextPage:   # Checking if there are further pages
            return []   # If no page, returning empty list

        next_page = page + 1   # Calculating page number of next page
        name = "Next Page (%d)" % (next_page)   # Naming the next page
        offset = (re.compile("offset=(.+?)&").findall(hasNextPage))[0]   # Extracting offset value
        return self._parse_view({'name': name, 'url': base_url % (offset, next_page), 'image': 'next.png', 'plot': None, 'fanart': 'next.png'})   # Returning the dictionary with next page details

    def watchlist(self):
        return self._process_watchlist_view('', "watchlist_page/%d", page=1)   # Returning processed watchlist information

    def _base_watchlist_view(self, res):
        base = {   # Base dictionary containing common keys and values for all watchlists
            "name": res[0],
            "url": 'watchlist_status_type/%s/%s' % (self._NAME, res[1]),
            "image": res[0].lower() + '.png',
            "plot": '',
        }

        return self._parse_view(base)   # Returning the dictionary with watchlist details after parsing it

    def _process_watchlist_view(self, params, base_plugin_url, page):
        all_results = list(map(self._base_watchlist_view, self.__mal_statuses()))   # Processing all results of users watchlist
        all_results = list(itertools.chain(*all_results))  # Combining all the lists of results
        return all_results   # Return the processed watchlist data

    def __mal_statuses(self):
        statuses = [   # List of possible watchlist status titles
            ("Next Up", "watching?next_up=true"),
            ("Currently Watching", "watching"),
            ("Completed", "completed"),
            ("On Hold", "on_hold"),
            ("Dropped", "dropped"),
            ("Plan to Watch", "plan_to_watch"),
            ("All Anime", ""),
        ]

        return statuses   # Return the list of statuses available in anime watchlist

    def get_watchlist_status(self, status, next_up, offset=0, page=1):
        # define a list of fields to be included in the response
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

        # define request params
        params = {
            "status": status,
            "sort": self.__get_sort(),
            "limit": 100,
            "offset": offset,
            "fields": ','.join(fields),
        }

        # construct API URL
        url = self._to_url("users/@me/animelist")

        # make GET request and return results using helper method
        return self._process_status_view(url, params, next_up, "watchlist_status_type_pages/mal/%s/%%s/%%d" % status, page)

    def get_watchlist_anime_entry(self, anilist_id):
        # get MAL mapping ID for the given AniList ID
        mal_id = self._get_mapping_id(anilist_id, 'mal_id')

        # if there is no corresponding MAL ID, return nothing
        if not mal_id:
            return

        # define request params
        params = {
            "fields": 'my_list_status',
        }

        # construct API URL and make GET request
        url = self._to_url("users/@me/animelist")
        results = self._get_request(url, headers=self.__headers(), params=params)

        # parse JSON response and extract relevant information
        results = json.loads(results)['data'][0]['node']['my_list_status']
        anime_entry = {}
        anime_entry['eps_watched'] = results['num_episodes_watched']
        anime_entry['status'] = results['status'].title()
        anime_entry['score'] = results['score']

        return anime_entry

    def _process_status_view(self, url, params, next_up, base_plugin_url, page):
        # make GET request and parse JSON response
        results = self._get_request(url, headers=self.__headers(), params=params)
        results = json.loads(results)

        # extract relevant data from API response
        if next_up:
            all_results = list(map(self._base_next_up_view, results['data']))
        else:
            all_results = list(map(self._base_watchlist_status_view, results['data']))

        all_results = list(itertools.chain(*all_results))
        all_results += self._handle_paging(results['paging'].get('next'), base_plugin_url, page)

        return all_results

    def _base_watchlist_status_view(self, res):
        info = {}

        # extract synopsis from response and add to info dict
        try:
            info['plot'] = res['node']['synopsis']
        except:
            pass

        # extract title from response and add to info dict
        title = res['node'].get('title')
        if self._title_lang == 'english':
            title = res['node'].get('alternative_titles').get('en') or title
        info['title'] = title

        # extract episode duration, genre, status, start date, studio, rating and mpaa rating from response and add to info dict
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

        # add media type to info dict
        info['mediatype'] = 'tvshow'

        # construct base view object
        base = {
            "name": '%s - %s/%s' % (title, res['list_status']["num_episodes_watched"], res['node']["num_episodes"]),
            "url": "watchlist_to_ep/%s/%s" % (res['node']['id'], res['list_status']["num_episodes_watched"]),
            "image": res['node']['main_picture'].get('large', res['node']['main_picture']['medium']),
            "plot": info,
        }

        # if media type is a movie with only one episode, update URL and mediatype accordingly
        if res['node']['media_type'] == 'movie' and res['node']["num_episodes"] == 1:
            base['url'] = "watchlist_to_movie/%s" % (res['node']['id'])
            base['plot']['mediatype'] = 'movie'
            return self._parse_view(base, False)

        return self._parse_view(base)

    # This function takes in a dictionary as an argument 'res' and returns a view for the next episode of an anime series.
    def _base_next_up_view(self, res):

        # Extracting necessary details from 'res' dictionary
        mal_id = res['node']['id']
        progress = res['list_status']["num_episodes_watched"]
        next_up = progress + 1
        episode_count = res['node']["num_episodes"]
        base_title = res['node'].get('title')

        # Checking if the language is English and altering the title accordingly
        if self._title_lang == 'english':
            base_title = res['node'].get('alternative_titles').get('en') or base_title

        title = '%s - %s/%s' % (base_title, next_up, episode_count)
        poster = image = res['node']['main_picture'].get('large', res['node']['main_picture']['medium'])
        plot = aired = None

        # Calling a private method '_get_next_up_meta' for getting more information about the next episode
        anilist_id, next_up_meta = self._get_next_up_meta(mal_id, int(progress))

        # Checking if meta information was returned by '_get_next_up_meta'
        if next_up_meta:
            url = 'play/%d/%d/' % (anilist_id, next_up)

            # Altering title, image, plot and aired variables based on the meta information
            if next_up_meta.get('title'):
                title = '%s - %s' % (title, next_up_meta.get('title'))
            if next_up_meta.get('image'):
                image = next_up_meta.get('image')
            plot = next_up_meta.get('plot')
            aired = next_up_meta.get('aired')

        # Creating a dictionary 'info' with the extracted details
        info = {}
        info['episode'] = next_up
        info['title'] = title
        info['tvshowtitle'] = res['node']['title']
        info['duration'] = res['node']['average_episode_duration']
        info['plot'] = plot
        info['mediatype'] = 'episode'
        info['aired'] = aired

        # Creating a dictionary 'base' with the extracted and altered information
        base = {
            "name": title,
            "url": "watchlist_to_ep/%s//%s" % (res['node']['id'], res['list_status']["num_episodes_watched"]),
            "image": image,
            "plot": info,
            "fanart": image,
            "poster": poster,
        }

        # Checking if meta information was returned by '_get_next_up_meta'
        if next_up_meta:
            base['url'] = url
            return self._parse_view(base, False)

        # Checking if the series is a movie and altering the dictionary 'base' accordingly
        if res['node']['media_type'] == 'movie' and res['node']["num_episodes"] == 1:
            base['url'] = "watchlist_to_movie/%s" % (res['node']['id'])
            base['plot']['mediatype'] = 'movie'
            return self._parse_view(base, False)

        return self._parse_view(base)

    # A private method '__headers' that returns the required headers for API calls
    def __headers(self):
        header = {
            'Authorization': "Bearer {}".format(self._token),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        return header

    # A method '_kitsu_to_mal_id' that takes in an argument 'kitsu_id' and returns the corresponding MAL ID
    def _kitsu_to_mal_id(self, kitsu_id):
        arm_resp = self._get_request("https://arm.now.sh/api/v1/search?type=kitsu&id=" + kitsu_id)
        if not arm_resp:
            raise Exception("AnimeID not found")

        mal_id = json.loads(arm_resp)["services"]["mal"]
        return mal_id

    # A method 'watchlist_update' that takes in an argument 'anilist_id' and 'episode' and updates the watchlist accordingly
    def watchlist_update(self, anilist_id, episode):

        # Getting MAL ID from AniList ID using a private method '_get_mapping_id'
        mal_id = self._get_mapping_id(anilist_id, 'mal_id')

        # If no mapping exists, return
        if not mal_id:
            return

        # Creating URL and data for PUT request and returning a lambda function that calls a private method '__update_watchlist'
        url = self._to_url("anime/%s/my_list_status" % (mal_id))
        data = {
            'num_watched_episodes': int(episode)
        }

        return lambda: self.__update_watchlist(anilist_id, episode, url, data)

    # A private method '__update_watchlist' that updates the watchlist
    def __update_watchlist(self, anilist_id, episode, url, data):
        _ = self._put_request(url, data=data, headers=self.__headers())

    # A private method '__get_sort' that returns the sort type based on the current sorting preference
    def __get_sort(self):
        sort_types = {
            "Anime Title": "anime_title",
            "Last Updated": "list_updated_at",
            "Anime Start Date": "anime_start_date",
            "List Score": "list_score"
        }

        return sort_types[self._sort]

    # A method 'watchlist_append' that takes in an argument 'anilist_id' and adds it to the watchlist
    def watchlist_append(self, anilist_id):
        # Getting MAL ID from AniList ID using a private method '_get_mapping_id'
        mal_id = self._get_mapping_id(anilist_id, 'mal_id')

        # If no mapping exists, return
        if not mal_id:
            return

        # Creating URL and data for PUT request and adding it to the watchlist
        url = self._to_url("anime/%s/my_list_status" % (mal_id))
        data = {'status': 'plan_to_watch'}
        result = json.loads(self._put_request(url, data=data, headers=self.__headers()))

        # Notifying the user that the anime was added to the watchlist
        if result.get('status'):
            control.notify('Added to Watchlist')
        return

    # A method 'watchlist_remove' that removes an anime from the watchlist
    def watchlist_remove(self, mal_id):
        url = self._to_url("anime/%s/my_list_status" % (mal_id))

        # Making a DELETE request to remove the anime from the watchlist
        _ = self._delete_request(url, headers=self.__headers())

        # Notifying the user that the anime was removed from the watchlist
        control.notify('Removed from Watchlist')
        return

    def watchlist_completed(self, anilist_id='', mal_id='', kitsu_id=''):
        if not mal_id:
            mal_id = self._get_mapping_id(anilist_id, 'mal_id')

        # If no mapping exists, return
        if not mal_id:
            return

        # Creating URL and data for PUT request and adding it to the watchlist
        url = self._to_url("anime/%s/my_list_status" % (mal_id))
        data = {'status': 'completed'}
        result = json.loads(self._put_request(url, data=data, headers=self.__headers()))

        # Notifying the user that the anime was added to the watchlist
        if result.get('status'):
            control.notify('Marked as Completed')
        return
