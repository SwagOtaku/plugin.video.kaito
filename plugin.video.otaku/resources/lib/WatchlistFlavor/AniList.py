import itertools
import json
import pickle
import random

import six
from resources.lib.ui import control, database, get_meta
from resources.lib.WatchlistFlavor.WatchlistFlavorBase import \
    WatchlistFlavorBase


class AniListWLF(WatchlistFlavorBase):
    _URL = "https://graphql.anilist.co"
    _TITLE = "AniList"
    _NAME = "anilist"
    _IMAGE = "anilist.png"

    # This function logs into the website and retrieves the userID for the watchlist
    def login(self):
    
        # Define the GraphQL query to retrieve user id
        query = '''
        query ($name: String) {
            User(name: $name) {
                id
                }
            }
        '''
    
        # Define the variables for the GraphQL query
        variables = {
            "name": self._username
        }
    
        # Make a POST request with the query and variables
        result = self._post_request(self._URL, headers=self.__headers(), json={'query': query, 'variables': variables})
        results = json.loads(result)
    
        # Check if there are errors in the results
        if "errors" in results.keys():
            return
    
        # Retrieve the user id from the results
        userId = results['data']['User']['id']
    
        # Package up the user id for returning
        login_data = {
            'userid': str(userId)
        }
    
        return login_data
    
    
    # This function retrieves the watchlist from the website
    def watchlist(self):
        return self._process_watchlist_view("watchlist/%d", page=1)
    
    
    # This function creates a base dictionary with information about an anime
    def _base_watchlist_view(self, res):
        base = {
            "name": res[0],
            "url": 'watchlist_status_type/%s/%s' % (self._NAME, res[1]),
            "image": res[0].lower() + '.png',
            "plot": '',
        }
    
        return self._parse_view(base)
    
    
    # This function processes the watchlist view by getting data for each anime in the user's status lists
    def _process_watchlist_view(self, base_plugin_url, page):
        all_results = list(map(self._base_watchlist_view, self.__anilist_statuses()))
        all_results = list(itertools.chain(*all_results))
        return all_results
    
    
    # This function retrieves all valid Anilist status types
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
    
    
    # This function gets the watchlist status for a specific user and status type
    def get_watchlist_status(self, status, next_up):
        # Define the GraphQL query to retrieve watchlist status
        query = '''
        query ($userId: Int, $userName: String, $status: MediaListStatus, $type: MediaType, $sort: [MediaListSort]) {
            MediaListCollection(userId: $userId, userName: $userName, status: $status, type: $type, sort: $sort) {
                lists {
                    entries {
                        ...mediaListEntry
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
                bannerImage
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
                countryOfOrigin
                averageScore
                characters (
                    page: 1,
                    sort: ROLE,
                    perPage: 10,
                ) {
                    edges {
                        node {
                            name {
                                userPreferred
                            }
                        }
                        voiceActors (language: JAPANESE) {
                            name {
                                userPreferred
                            }
                            image {
                                large
                            }
                        }
                    }
                }
                studios {
                    edges {
                        node {
                            name
                        }
                    }
                }
                trailer {
                    id
                    site
                }
            }
        }
        '''
    
        # Define the variables for the GraphQL query
        variables = {
            'userId': int(self._user_id),
            'username': self._username,
            'status': status,
            'type': 'ANIME',
            'sort': self.__get_sort()
        }
    
        # Process the status view using the GraphQL query and variables
        return self._process_status_view(query, variables, next_up, "watchlist/%d", page=1)
    
    
    # This function gets the watchlist entry for a specific anime
    def get_watchlist_anime_entry(self, anilist_id):
        # Define the GraphQL query to retrieve the watchlist entry for an anime
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
    
        # Define the variables for the GraphQL query
        variables = {
            'mediaId': anilist_id
        }
    
        # Make a POST request with the query and variables
        result = self._post_request(self._URL, headers=self.__headers(), json={'query': query, 'variables': variables})
        results = json.loads(result)['data']['Media']['mediaListEntry']
    
        # Convert the results into a dictionary with relevant information about the anime
        anime_entry = {}
        anime_entry['eps_watched'] = results['progress']
        anime_entry['status'] = results['status'].title()
        anime_entry['score'] = results['score']
    
        return anime_entry
    

    # This method sends a post request to URL with 'query' and 'variables' as json payload,
    # then parses the result and returns a list containing entries from MediaListCollection['lists'].
    # next_up: boolean that indicates whether to return next-up data or full watchlist data.
    # base_plugin_url: base url for generating plugin urls.
    # page: page number for pagination purposes.
    def _process_status_view(self, query, variables, next_up, base_plugin_url, page):
        # Make a post request with 'query' and 'variables' in json format, and store the result in a variable.
        result = self._post_request(self._URL, headers=self.__headers(), json={'query': query, 'variables': variables})
        # Parse the result as a json object and store it in another variable.
        results = json.loads(result)

        # Check if there are any errors in the result and return None if so.
        if "errors" in results.keys():
            return

        # Create an empty list called entries.
        entries = []
        # Iterate through all lists in the MediaListCollection and append their entries into the entries list.
        lists = results['data']['MediaListCollection']['lists']
        for mlist in lists:
            entries += mlist['entries']

        # Collect metadata for each entry using a helper method.
        _ = get_meta.collect_meta(entries)

        # Based on the value of 'next_up', map either '_base_next_up_view' or '_base_watchlist_status_view'
        # on reversed entries and store the result in a variable called 'all_results'.
        if next_up:
            all_results = list(map(self._base_next_up_view, reversed(entries)))
        else:
            all_results = list(map(self._base_watchlist_status_view, reversed(entries)))

        # Filter out any 'None' values from the all_results list.
        all_results = [i for i in all_results if i is not None]

        # Flatten the multiple lists within all_results into a single list.
        all_results = list(itertools.chain(*all_results))

        # Return the final list of results.
        return all_results

    # This method takes in a response from MediaListCollection and returns a dictionary containing metadata about it.
    def _base_watchlist_status_view(self, res):
        # Get the progress value and media data from response.
        progress = res['progress']
        res = res['media']

        # If media status is 'RELEASING', remove the cached episodes for this media that are older than five days.
        if res.get('status') == 'RELEASING':
            from datetime import date
            ep_list = database.get_episode_list(res['id'])
            if ep_list:
                last_updated = ep_list[0]['last_updated']
                if six.PY2:
                    year, month, day = last_updated.split('-')
                    ldate = date(int(year), int(month), int(day))
                else:
                    ldate = date.fromisoformat(last_updated)
                ldiff = date.today() - ldate
                if ldiff.days >= 5:
                    database.remove_episodes(res['id'])

        # Create a dictionary to store metadata about the media.
        info = {}

        # Store genres, plot, title, duration, aired date, status, media type, country, cast,
        # studio, rating, and trailer for the media entry (if available) into the info dictionary.
        info['genre'] = res.get('genres')

        desc = res.get('description')
        if desc:
            desc = desc.replace('<i>', '[I]').replace('</i>', '[/I]')
            desc = desc.replace('<b>', '[B]').replace('</b>', '[/B]')
            desc = desc.replace('<br>', '[CR]')
            desc = desc.replace('\n', '')
            info['plot'] = desc.encode('utf-8') if six.PY2 else desc

        title = res['title'].get(self._title_lang) or res['title'].get('userPreferred')
        info['title'] = title.encode('utf-8') if six.PY2 else title

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

        info['country'] = res.get('countryOfOrigin', '')

        try:
            cast = []
            cast2 = []
            for x in res.get('characters').get('edges'):
                role = x.get('node').get('name').get('userPreferred')
                actor = x.get('voiceActors')[0].get('name').get('userPreferred')
                actor_hs = x.get('voiceActors')[0].get('image').get('large')
                cast.append((actor, role))
                cast2.append({'name': actor, 'role': role, 'thumbnail': actor_hs})
            info['cast'] = cast
            info['cast2'] = cast2
        except:
            pass

        try:
            info['studio'] = [x.get('node').get('name') for x in res.get('studios').get('edges')]
        except:
            pass

        try:
            info['rating'] = res.get('averageScore') / 10.0
        except:
            pass

        try:
            if res.get('trailer').get('site') == 'youtube':
                info['trailer'] = 'plugin://plugin.video.youtube/play/?video_id={0}'.format(res.get('trailer').get('id'))
            else:
                info['trailer'] = 'plugin://plugin.video.dailymotion_com/?url={0}&mode=playVideo'.format(res.get('trailer').get('id'))
        except:
            pass

        # Create a base dictionary containing basic metadata about the media.
        base = {
            "name": '%s - %d/%d' % (title, progress, res['episodes'] if res['episodes'] is not None else 0),
            "url": "watchlist_query/%s/%s/%d" % (res['id'], res.get('idMal'), progress),
            "image": res['coverImage']['extraLarge'],
            "poster": res['coverImage']['extraLarge'],
            "fanart": res['coverImage']['extraLarge'],
            "banner": res.get('bannerImage'),
            "plot": info
        }

        # If there's already some metadata present in the database, update the base dictionary with that metadata.
        show_meta = database.get_show_meta(res['id'])
        if show_meta:
            art = pickle.loads(show_meta['art'])
            if art.get('fanart'):
                base['fanart'] = random.choice(art.get('fanart'))
            if art.get('thumb'):
                base['landscape'] = random.choice(art.get('thumb'))
            if art.get('clearart'):
                base['clearart'] = random.choice(art.get('clearart'))
            if art.get('clearlogo'):
                base['clearlogo'] = random.choice(art.get('clearlogo'))

        # If the media format is 'MOVIE' and episodes count is 1, update url and mediatype fields in base dictionary
        # and return the parsed base dictionary.
        if res['format'] == 'MOVIE' and res['episodes'] == 1:
            base['url'] = "watchlist_to_movie/?anilist_id=%s" % (res['id'])
            base['plot']['mediatype'] = 'movie'
            return self._parse_view(base, False)

        # Return the parsed base dictionary.
        return self._parse_view(base)


    def _base_next_up_view(self, res):
        progress = res['progress']
        res = res['media']
    
        # Assign values for next episode
        next_up = progress + 1
        episode_count = res['episodes'] if res['episodes'] is not None else 0
        base_title = res['title'].get(self._title_lang) or res['title'].get('userPreferred')
        title = '%s - %s/%s' % (base_title, next_up, episode_count)
        poster = image = res['coverImage']['extraLarge']
        plot = aired = None
    
        # Check if there are no more episodes or if the next episode is airing
        if episode_count > 0 and next_up > episode_count:
            return None
    
        if res['nextAiringEpisode'] is not None and next_up == res['nextAiringEpisode']['episode']:
            return None
    
        # Get metadata for the next episode
        anilist_id, next_up_meta = self._get_next_up_meta('', progress, res['id'])
        if next_up_meta:
            url = 'play/%d/%d/' % (anilist_id, next_up)
            if next_up_meta.get('title'):
                title = '%s - %s' % (title, next_up_meta.get('title'))
            if next_up_meta.get('image'):
                image = next_up_meta.get('image')
            plot = next_up_meta.get('plot')
            aired = next_up_meta.get('aired')
    
        info = {}
    
        # Add show information to dictionary
        try:
            info['genre'] = res.get('genres')
        except:
            pass
        info['episode'] = next_up
        info['title'] = title
        info['tvshowtitle'] = res['title']['userPreferred']
        info['plot'] = plot
        info['mediatype'] = 'episode'
        info['aired'] = aired
    
        # Create dictionary for base information
        base = {
            "name": title,
            "url": "watchlist_query/%s/%s/%d" % (res['id'], res.get('idMal'), progress),
            "image": image,
            "plot": info,
            "fanart": image,
            "poster": poster,
        }
    
        # Add metadata for show
        show_meta = database.get_show_meta(res['id'])
        if show_meta:
            art = pickle.loads(show_meta['art'])
            if art.get('fanart'):
                base['fanart'] = random.choice(art.get('fanart'))
            if art.get('thumb'):
                base['landscape'] = random.choice(art.get('thumb'))
            if art.get('clearart'):
                base['clearart'] = random.choice(art.get('clearart'))
            if art.get('clearlogo'):
                base['clearlogo'] = random.choice(art.get('clearlogo'))
    
        # Check if there is metadata for next episode, and whether it's a movie with one episode
        if next_up_meta:
            base['url'] = url
            return self._parse_view(base, False)
    
        if res['format'] == 'MOVIE' and res['episodes'] == 1:
            base['url'] = "watchlist_to_movie/?anilist_id=%s" % (res['id'])
            base['plot']['mediatype'] = 'movie'
            return self._parse_view(base, False)
    
        return self._parse_view(base)
    
    
    def _get_titles(self, res):
        # Get titles of a show
        titles = list(set(res['title'].values())) + res.get('synonyms', [])[:2]
        if res['format'] == 'MOVIE':
            titles = list(res['title'].values())
        # Filter out non-ascii characters in the titles
        titles = [x for x in titles if (all(ord(char) < 128 for char in x) if x else [])]
        titles = '|'.join(titles[:3])
        return titles
    
    
    def __get_sort(self):
        # Sort types for the watchlist
        sort_types = {
            "Score": "SCORE",
            "Progress": "PROGRESS",
            "Last Updated": "UPDATED_TIME",
            "Last Added": "ADDED_TIME",
            "Romaji Title": "MEDIA_TITLE_ROMAJI_DESC",
            "English Title": "MEDIA_TITLE_ENGLISH_DESC"
        }
        return sort_types[self._sort]
    
    
    def __headers(self):
        # Headers for authorization
        headers = {
            'Authorization': 'Bearer ' + self._token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        return headers
    
    
    def _kitsu_to_anilist_id(self, kitsu_id):
        # Convert Kitsu ID to Anilist ID
        arm_resp = self._get_request("https://arm.now.sh/api/v1/search?type=kitsu&id=" + kitsu_id)
        if not arm_resp:
            raise Exception("AnimeID not found")
        anilist_id = json.loads(arm_resp)["services"]["anilist"]
        return anilist_id
    
    
    def watchlist_update(self, anilist_id, episode):
        # Update the status of a show in the user's watchlist
        return lambda: self.__update_library(episode, anilist_id)
    
    
    def __update_library(self, episode, anilist_id):
        # Mutation to update the status of a show in the user's watchlist
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
    
    
    def watchlist_append(self, anilist_id):
        # Add a show to the user's watchlist
        result = json.loads(self.__update_planning(anilist_id))
        if result.get('data').get('SaveMediaListEntry'):
            control.notify('Added to Watchlist')
        return
    
    
    def __update_planning(self, anilist_id):
        # Mutation to add a show to the user's watchlist
        query = '''
        mutation ($mediaId: Int, $status: MediaListStatus) {
            SaveMediaListEntry (mediaId: $mediaId, status: $status) {
                id
                status
                }
            }
        '''
        variables = {
            'mediaId': int(anilist_id),
            'status': 'PLANNING'
        }
        return self._post_request(self._URL, headers=self.__headers(), json={'query': query, 'variables': variables})
    
    
    def watchlist_remove(self, anilist_id):
        # Remove a show from the user's watchlist
        item_id = self.__get_item_id(anilist_id)
        result = self.__delete_item(item_id)
        if result:
            control.notify('Removed from Watchlist')
        return
    
    
    def __get_item_id(self, anilist_id):
        # Get the item ID of a show in the user's watchlist
        query = '''
        query ($mediaId: Int) {
            Media (id: $mediaId) {
                mediaListEntry {
                    id
                    }
                }
            }
        '''
        variables = {
            'mediaId': int(anilist_id),
        }
        res = json.loads(self._post_request(self._URL, headers=self.__headers(), json={'query': query, 'variables': variables}))
        return res.get('data').get('Media').get('mediaListEntry').get('id')
    
    
    def __delete_item(self, anilist_id):
        # Mutation to delete an item from the user's watchlist
        query = '''
        mutation ($id: Int) {
            DeleteMediaListEntry (id: $id) {
                deleted
                }
            }
        '''
        variables = {
            'id': int(anilist_id),
        }
        res = json.loads(self._post_request(self._URL, headers=self.__headers(), json={'query': query, 'variables': variables}))
        return res.get('data').get('DeleteMediaListEntry').get('deleted')
    