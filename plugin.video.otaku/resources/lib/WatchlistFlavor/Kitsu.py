import itertools
import json
import time

from resources.lib.ui import control
from resources.lib.WatchlistFlavor.WatchlistFlavorBase import \
    WatchlistFlavorBase
from six.moves import urllib_parse


class KitsuWLF(WatchlistFlavorBase):
    _URL = "https://kitsu.io/api"
    _TITLE = "Kitsu"
    _NAME = "kitsu"
    _IMAGE = "kitsu.png"
    _mapping = None

    # This function performs the login process for a user
    def login(self):
        # Set parameters for authentication request
        params = {
            "grant_type": "password",
            "username": self._auth_var,
            "password": self._password
        }

        # Send post request to obtain token
        resp = self._post_request(self._to_url("oauth/token"), params=params, json='')

        # If response is empty, return None
        if not resp:
            return

        # Load JSON data from response and set access token
        data = json.loads(resp)
        self._token = data['access_token']

        # Get user info
        resp2 = self._get_request(self._to_url("edge/users"), headers=self.__headers(), params={'filter[self]': True})
        data2 = json.loads(resp2)["data"][0]

        # Set login data object with relevant information
        login_data = {
            'username': data2["attributes"]["name"],
            'userid': data2['id'],
            'token': data['access_token'],
            'refresh': data['refresh_token'],
            'expiry': str(time.time() + int(data['expires_in']))
        }

        # Return login data object
        return login_data

    # Define a function to refresh the token
    def refresh_token(self):
        # Create a dictionary with required parameters for refreshing the token
        params = {
            "grant_type": "refresh_token",
            "refresh_token": control.getSetting('kitsu.refresh'),  # Get the refresh token from the Kitsu platform
        }
        # Send a post request to get the access token
        resp = self._post_request(self._to_url("oauth/token"), params=params, json='')

        # If no response obtained, return None
        if not resp:
            return

        # Load the JSON data returned by the server in resp variable
        data = json.loads(resp)
        # Update the token, refresh token and expiry time in the Kitsu api settings
        control.setSetting('kitsu.token', data['access_token'])
        control.setSetting('kitsu.refresh', data['refresh_token'])
        control.setSetting('kitsu.expiry', str(time.time() + int(data['expires_in'])))

    # Define a function to create headers containing content type, accept and authorization values
    def __headers(self):
        # Define a dictionary of headers with Content-Type, Accept and Authorization keys
        headers = {
            'Content-Type': 'application/vnd.api+json',
            'Accept': 'application/vnd.api+json',
            'Authorization': "Bearer {}".format(self._token),  # Use the _token attribute as the value for the token key
        }
        # Return the headers dictionary
        return headers

    # Define a function to handle pagination
    def _handle_paging(self, hasNextPage, base_url, page):
        # If there are no more pages left to load, return an empty list
        if not hasNextPage:
            return []
        # Calculate the next page number
        next_page = page + 1
        name = "Next Page (%d)" % (next_page)  # Create a string with the format "Next Page (page_number)"
        # Parse the url of the next page to retrieve the offset value
        parsed = urllib_parse.urlparse(hasNextPage)
        offset = urllib_parse.parse_qs(parsed.query)['page[offset]'][0]
        # Return the results obtained from parsing the base URL along with the calculated offset and next page number
        return self._parse_view({'name': name, 'url': base_url % (offset, next_page), 'image': 'next.png', 'plot': None, 'fanart': 'next.png'})

    # Define a function to get the watchlist data
    def watchlist(self):
        # Create a dictionary to filter the search results by user ID
        params = {"filter[user_id]": self._user_id}
        # Get the URL for the user's library-entries resources
        url = self._to_url("edge/library-entries")
        # Process the watchlist status view using the URL, parameters and page number 1
        return self._process_watchlist_status_view(url, params, "watchlist/%d", page=1)

    # Define a function to return the base watchlist status view
    def _base_watchlist_status_view(self, res):
        # Create a base dictionary with minimal keys and update it with response parameter passed
        base = {
            "name": res[0],
            "url": 'watchlist_status_type/%s/%s' % (self._NAME, res[1]),
            "image": res[0].lower() + '.png',
            "plot": '',
        }
        # Return the parsed view obtained from the base dictionary
        return self._parse_view(base)

    # Define a function to process and get the watchlist status view
    def _process_watchlist_status_view(self, url, params, base_plugin_url, page):
        # Get the list of all statuses for watchlist
        all_results = list(map(self._base_watchlist_status_view, self.__kitsu_statuses()))
        # Flatten the resulting nested list into a single list
        all_results = list(itertools.chain(*all_results))
        # Return all results obtained
        return all_results

    # Define a function to get the Kitsu statuses
    def __kitsu_statuses(self):
        # Create a list of tuples with status name and corresponding URL parameter
        statuses = [
            ("Next Up", "current?next_up=true"),
            ("Current", "current"),
            ("Want to Watch", "planned"),
            ("Completed", "completed"),
            ("On Hold", "on_hold"),
            ("Dropped", "dropped"),
        ]
        # Return the statuses list
        return statuses

    # This function gets the watchlist status of a user for a particular anime
    # based on their status (e.g. "current"), the next episode up, an offset value,
    # and a page number. It then processes the view with more information and returns it.
    def get_watchlist_status(self, status, next_up, offset=0, page=1):
        # Set the URL to access certain fields for each anime entry in the library
        url = self._to_url("edge/library-entries")

        # Set the parameters for the request to the API endpoint
        params = {
            "fields[anime]": "titles,canonicalTitle,posterImage,episodeCount,synopsis,episodeLength,subtype,averageRating,ageRating,youtubeVideoId",
            "filter[user_id]": self._user_id,
            "filter[kind]": "anime",
            "filter[status]": status,
            "include": "anime,anime.mappings,anime.mappings.item",
            "page[limit]": "50",
            "page[offset]": offset,
            "sort": self.__get_sort(),  # Get a specific sorting mechanism based on the class instance
        }

        # Use another method to process the view with additional information
        return self._process_watchlist_view(
            url, params, next_up,
            "watchlist_status_type_pages/kitsu/%s/%%s/%%d" % status, page)

    # This function is called by get_watchlist_status() to add additional information
    # to the view that was retrieved from the API. It returns the modified results.
    def _process_watchlist_view(self, url, params, next_up, base_plugin_url, page):
        # Send a GET request to the URL with the given parameters
        result = self._get_request(url, headers=self.__headers(), params=params)

        # Convert the result to a Python dictionary object
        result = json.loads(result)

        # Set the entries list as the anime objects in the result.
        _list = result["data"]

        # If there are no included anime objects, create an empty list.
        if not result.get('included'):
            result['included'] = []

        el = result["included"][:len(_list)]

        # self._mapping = filter(lambda x: x['type'] == 'mappings', result['included'])
        # Use list comprehension to get the "mappings" objects from the included list
        # This is used later to map the IDs of anime objects between sites like MyAnimeList and Kitsu.
        self._mapping = [x for x in result['included'] if x['type'] == 'mappings']

        # Run various functions based on whether or not the user has specified a value for "next_up"
        # Returns a list of all the available results as dictionaries.
        if next_up:
            all_results = list(map(self._base_next_up_view, _list, el))
        else:
            all_results = list(map(self._base_watchlist_view, _list, el))

        # Flatten the list of results with itertools.chain(*iterables), which returns a new iterator
        all_results = list(itertools.chain(*all_results))

        # Add any additional pages to the view, as needed
        all_results += self._handle_paging(result['links'].get('next'), base_plugin_url, page)

        return all_results

    # This function is called by _process_watchlist_view() for each anime entry that was found in the API response
    # It creates a new dictionary with additional information for the given anime entry and returns it.
    def _base_watchlist_view(self, res, eres):
        # Get the ID of the mapping object for the current anime entry
        _id = eres['id']
        mal_id = self._mapping_mal(_id)

        # Initialize a dictionary for various information about the anime entry
        info = {}

        # Attempt to get and set various attributes of the anime.
        try:
            info['plot'] = eres['attributes'].get('synopsis')
        except:
            pass

        try:
            info['title'] = eres["attributes"]["titles"].get(self.__get_title_lang(), eres["attributes"]['canonicalTitle'])
        except:
            pass

        try:
            info['duration'] = eres['attributes']['episodeLength'] * 60
        except:
            pass

        try:
            info['rating'] = float(eres['attributes']['averageRating']) / 10
        except:
            pass

        try:
            info['mpaa'] = eres['attributes']['ageRating']
        except:
            pass

        try:
            info['trailer'] = 'plugin://plugin.video.youtube/play/?video_id={0}'.format(eres['attributes']['youtubeVideoId'])
        except:
            pass

        # Set the media type as a TV show, since the request is for anime entries.
        info['mediatype'] = 'tvshow'

        # Create a base dictionary with basic information about the anime entry
        base = {
            "name": '%s - %d/%d' % (
                eres["attributes"]["titles"].get(
                    self.__get_title_lang(), eres["attributes"]['canonicalTitle']),
                res["attributes"]['progress'],
                eres["attributes"]['episodeCount']
                if eres["attributes"]['episodeCount'] is not None else 0),
            "url": "watchlist_to_ep/%s/%s/%s" % (mal_id, _id, res["attributes"]['progress']),
            "image": eres["attributes"]['posterImage']['large'],
            "plot": info,
        }

        # If the anime is a movie, set the base dictionary's URL to view the entry as a movie
        if eres['attributes']['subtype'] == 'movie' and eres['attributes']['episodeCount'] == 1:
            base['url'] = "watchlist_to_movie/%s" % (mal_id)
            base['plot']['mediatype'] = 'movie'

            # Return the modified dictionary
            return self._parse_view(base, False)

        # Return the modified dictionary
        return self._parse_view(base)

    # This method generates the entry for the next episode of a show in the watchlist
    # It takes the response from the Kitsu API and the corresponding media ID from MyAnimeList
    def _base_next_up_view(self, res, eres):
        # Extract the ID for the show in this response
        _id = eres['id']
        # Map this ID to the corresponding MyAnimeList ID
        mal_id = self._mapping_mal(_id)

        # Get relevant attributes from the JSON response
        progress = res["attributes"]['progress']
        next_up = progress + 1
        anime_title = eres["attributes"]["titles"].get(self.__get_title_lang(), eres["attributes"]['canonicalTitle'])
        episode_count = eres["attributes"]['episodeCount'] if eres["attributes"]['episodeCount'] is not None else 0
        # Construct the title for the episode
        title = '%s - %d/%d' % (anime_title, next_up, episode_count)
        poster = image = eres["attributes"]['posterImage']['large']
        plot = aired = None

        # Get additional meta information about the show
        anilist_id, next_up_meta = self._get_next_up_meta(mal_id, int(progress))
        if next_up_meta:
            url = 'play/%d/%d/' % (anilist_id, next_up)
            # If the meta information includes a title, add it to the original title
            if next_up_meta.get('title'):
                title = '%s - %s' % (title, next_up_meta.get('title'))
            # If the meta information includes an image, update the image for the episode
            if next_up_meta.get('image'):
                image = next_up_meta.get('image')
            plot = next_up_meta.get('plot')
            aired = next_up_meta.get('aired')
        info = {}

        # Build a dictionary of relevant episode information
        info['episode'] = next_up
        info['title'] = title
        info['tvshowtitle'] = anime_title
        info['plot'] = plot
        info['mediatype'] = 'episode'
        info['aired'] = aired

        # Build the dictionary entry for the episode
        base = {
            "name": title,
            # The URL for the episode contains information needed to play it
            "url": "watchlist_to_ep/%s/%s/%s" % (mal_id, _id, res["attributes"]['progress']),
            "image": image,
            "plot": info,
            "fanart": image,
            "poster": poster,
        }

        if next_up_meta:
            base['url'] = url
            # If there is meta information, return the parsed view based on that information
            return self._parse_view(base, False)

        # If this is a movie with only one episode, update the base dictionary to reflect that
        if eres['attributes']['subtype'] == 'movie' and eres['attributes']['episodeCount'] == 1:
            base['url'] = "watchlist_to_movie/%s" % (mal_id)
            base['plot']['mediatype'] = 'movie'
            # Return the parsed view based on the modified base dictionary
            return self._parse_view(base, False)

        # Otherwise, return the parsed view based on the original base dictionary
        return self._parse_view(base)

    # This method maps an AniList ID to a corresponding Kitsu ID
    def _mapping_mal(self, kitsu_id):
        mal_id = ''
        for i in self._mapping:
            if i['attributes']['externalSite'] == 'myanimelist/anime':
                if i['relationships']['item']['data']['id'] == kitsu_id:
                    mal_id = i['attributes']['externalId']
                    break

        return mal_id

    # This method retrieves the entry for a specific show in the watchlist
    # It takes an AniList ID as input
    def get_watchlist_anime_entry(self, anilist_id):
        # Get the corresponding Kitsu ID for this show
        kitsu_id = self._get_mapping_id(anilist_id, 'kitsu_id')

        if not kitsu_id:
            return

        # Build and execute a GET request for the metadata on this show's entry in the watchlist
        url = self._to_url("edge/library-entries")
        params = {
            "filter[user_id]": self._user_id,
            "filter[anime_id]": kitsu_id
        }
        result = self._get_request(url, headers=self.__headers(), params=params)
        result = json.loads(result)
        item_dict = result['data'][0]['attributes']

        anime_entry = {}
        # Get relevant attributes from the response
        anime_entry['eps_watched'] = item_dict['progress']
        anime_entry['status'] = item_dict['status']
        anime_entry['score'] = item_dict['ratingTwenty']

        # Return the dictionary of relevant information on this entry
        return anime_entry

    # This method updates the watchlist entry for a show to reflect that a new episode has been watched
    # It takes an AniList ID and the number of the episode watched as inputs
    def watchlist_update(self, anilist_id, episode):
        # Get the corresponding Kitsu ID for this show
        kitsu_id = self._get_mapping_id(anilist_id, 'kitsu_id')

        if not kitsu_id:
            return

        # Build and execute a GET request for the metadata on this show's entry in the watchlist
        url = self._to_url("edge/library-entries")
        params = {
            "filter[user_id]": self._user_id,
            "filter[anime_id]": kitsu_id
        }
        scrobble = self._get_request(url, headers=self.__headers(), params=params)
        item_dict = json.loads(scrobble)
        # If there is no existing entry, create one with the current episode count
        if len(item_dict['data']) == 0:
            return lambda: self.__post_params(url, episode, kitsu_id)

        # Otherwise, update the existing entry
        animeid = item_dict['data'][0]['id']
        return lambda: self.__patch_params(url, animeid, episode)

    # Define a method that constructs and sends a POST request to update the episode progress of an anime entry on Kitsu
    def __post_params(self, url, episode, kitsu_id):
        # Construct the request JSON body
        params = {
            "data": {
                "type": "libraryEntries",
                "attributes": {
                    'status': 'current',
                    'progress': int(episode)
                },
                "relationships": {
                    "user": {
                        "data": {
                            "id": self._user_id,
                            "type": "users"
                        }
                    },
                    "anime": {
                        "data": {
                            "id": int(kitsu_id),
                            "type": "anime"
                        }
                    }
                }
            }
        }
        # Send the POST request with the constructed JSON body
        self._post_request(url, headers=self.__headers(), json=params)

    # Define a method that constructs and sends a PATCH request to update the episode progress of an anime entry on Kitsu
    def __patch_params(self, url, animeid, episode):
        # Construct the request JSON body
        params = {
            'data': {
                'id': int(animeid),
                'type': 'libraryEntries',
                'attributes': {
                    'progress': int(episode)}
            }
        }
        # Send the PATCH request with the constructed JSON body
        self._patch_request("%s/%s" % (url, animeid), headers=self.__headers(), json=params)

    # Define a method that returns the sort type for displaying anime entries in a user's library on Kitsu
    def __get_sort(self):
        # Dictionary containing possible sort types and their corresponding sort parameters
        sort_types = {
            "Date Updated": "-progressed_at",
            "Progress": "-progress",
            "Title": "anime.titles." + self.__get_title_lang(),
        }
        # Return the corresponding sort parameter for the specified sort type
        return sort_types[self._sort]

    # Define a method that returns the language code for anime title based on user's preference
    def __get_title_lang(self):
        # Dictionary containing possible language preferences and their corresponding codes
        title_langs = {
            "Canonical": "canonical",
            "English": "en",
            "Romanized": "en_jp",
        }
        # Return the corresponding code for the specified language preference
        return title_langs[self._title_lang]

    # Define a method that adds an anime entry to a user's watchlist on Kitsu
    def watchlist_append(self, anilist_id):
        # Get the Kitsu ID of the anime entry based on its AniList ID
        kitsu_id = self._get_mapping_id(anilist_id, 'kitsu_id')
        if not kitsu_id:
            return
        # Construct the request JSON body
        url = self._to_url("edge/library-entries")
        params = {
            "data": {
                "type": "libraryEntries",
                "attributes": {
                    'status': 'planned',
                },
                "relationships": {
                    "user": {
                        "data": {
                            "id": self._user_id,
                            "type": "users"
                        }
                    },
                    "anime": {
                        "data": {
                            "id": int(kitsu_id),
                            "type": "anime"
                        }
                    }
                }
            }
        }
        # Send the POST request with the constructed JSON body and notify the user if successful
        result = json.loads(self._post_request(url, headers=self.__headers(), json=params))
        if result.get('data'):
            control.notify('Added to Watchlist')
        return

    # Define a method that removes an anime entry from a user's watchlist on Kitsu
    def watchlist_remove(self, mal_id):
        # Get the Kitsu ID of the anime entry based on its MyAnimeList ID
        kitsu_id = self._get_mapping_id_mal(mal_id, 'kitsu_id')
        if not kitsu_id:
            return
        # Construct the request parameters
        url = self._to_url("edge/library-entries")
        params = {
            "filter[user_id]": self._user_id,
            "filter[anime_id]": kitsu_id
        }
        # Send a GET request to retrieve the ID of the specified anime entry in the user's library
        result = self._get_request(url, headers=self.__headers(), params=params)
        item_id = json.loads(result).get('data')[0].get('id')
        # Send a DELETE request to remove the specified anime entry from the user's library and notify the user if successful
        url = self._to_url("edge/library-entries/%s" % (item_id))
        _ = self._delete_request(url, headers=self.__headers())
        control.notify('Removed from Watchlist')
        return
