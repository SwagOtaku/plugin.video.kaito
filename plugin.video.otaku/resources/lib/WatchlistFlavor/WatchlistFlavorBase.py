import json
import pickle
import random

from resources.lib.ui import client, control, database, utils


class WatchlistFlavorBase(object):
    _URL = None
    _TITLE = None
    _NAME = None
    _IMAGE = None

    # This is a constructor for the class which initializes all the instance variables
    def __init__(self, auth_var=None, username=None, password=None, user_id=None, token=None, refresh=None, sort=None, title_lang=None):

        # Check if self is of type WatchlistFlavorBase and raise exception if it is.
        if type(self) is WatchlistFlavorBase:
            raise Exception("Base Class should not be created")

        # Assign all instance variables according to the arguments passed in.
        self._auth_var = auth_var
        self._username = username
        self._password = password
        self._user_id = user_id
        self._token = token
        self._refresh = refresh
        self._sort = sort

        # If title_lang exists then assign it to _title_lang else set it according to control.getSetting("titlelanguage")
        if title_lang:
            self._title_lang = title_lang
        else:
            self._title_lang = self._get_title_lang(control.getSetting("titlelanguage"))

    # This is method to get title language as per the key provided.
    def _get_title_lang(self, title_key):

        # Define dictionary containing mapping of title keys with their corresponding languages.
        title_lang = {
            "40370": "userPreferred",
            "Romaji (Shingeki no Kyojin)": "userPreferred",
            "40371": "english",
            "English (Attack on Titan)": "english"
        }

        # Return the language corresponding to the title key passed in.
        return title_lang[title_key]

    # This is a class method to get the name of the current class.
    @classmethod
    def name(cls):

        # Raise an exception if the class variable _NAME is None.
        if cls._NAME is None:
            raise Exception("Missing Name")

        # Return the name of the class.
        return cls._NAME

    # These are property methods to get the values of the instance variables. They raise an exception if the variable is None.
    @property
    def image(self):
        if self._IMAGE is None:
            raise Exception("Missing Image")
        return self._IMAGE

    @property
    def title(self):
        if self._TITLE is None:
            raise Exception("Missing Title")
        return self._TITLE

    @property
    def url(self):
        if self._URL is None:
            raise Exception("Missing Url")
        return self._URL

    # This is a property method to get the flavor_name equal to _NAME instance variable.
    @property
    def flavor_name(self):
        return self._NAME

    @property
    def username(self):
        return self._username

    # These are abstract methods which should be implemented by subclass.
    def login(self):
        raise NotImplementedError("login should be implemented by subclass")

    def watchlist(self):
        raise NotImplementedError("watchlist should be implemented by subclass")

    def get_watchlist_status(self, status):
        raise NotImplementedError("get_watchlist_status should be implemented by subclass")

    def watchlist_update(self, episode, kitsu_id):
        raise NotImplementedError("watchlist_update should be implemented by subclass")

    def watchlist_append(self, anilist_id):
        raise NotImplementedError("watchlist_append should be implemented by subclass")

    def watchlist_remove(self, anilist_id):
        raise NotImplementedError("watchlist_append should be implemented by subclass")

    # This is a method to get next up metadata for the show.
    def _get_next_up_meta(self, mal_id, next_up, anilist_id=None):

        # Initialize the dictionary to store metadata.
        next_up_meta = {}

        # If anilist_id exists then get show from database using it else use mal_id.
        if anilist_id:
            show = database.get_show(anilist_id)
        else:
            show = database.get_show_mal(mal_id)

        # If show is not None then proceed.
        if show:

            # Get the anilist_id of the show and its metadata along with fanart image.
            anilist_id = show['anilist_id']
            show_meta = database.get_show_meta(anilist_id)

            if show_meta:
                art = pickle.loads(show_meta.get('art'))
                if art.get('fanart'):
                    next_up_meta['image'] = random.choice(art.get('fanart'))

            # Get episode list for the anilist id and if episodes exist then get metadata for next up episode.
            episodes = database.get_episode_list(show['anilist_id'])
            if episodes:
                try:
                    episode_meta = pickle.loads(episodes[next_up]['kodi_meta'])
                    next_up_meta['title'] = episode_meta['info']['title']
                    next_up_meta['image'] = episode_meta['image']['thumb']
                    next_up_meta['plot'] = episode_meta['info']['plot']
                    next_up_meta['aired'] = episodes[next_up]['air_date']
                except:
                    pass

            # If episodes don't exist but simkl_id does, get metadata for next up episode using simkl API.
            elif show['simkl_id']:
                try:
                    resp = database.get(client.request, 4, 'https://api.simkl.com/anime/episodes/%s?extended=full' % show['simkl_id'])
                    resp = json.loads(resp)
                    episode_meta = resp[next_up]
                    next_up_meta['title'] = episode_meta['title']
                    if episode_meta['img'] is not None:
                        next_up_meta['image'] = 'https://simkl.net/episodes/%s_w.jpg' % episode_meta['img']
                    next_up_meta['plot'] = episode_meta['description']
                except:
                    pass

        # Return the anilist_id and next up metadata.
        return anilist_id, next_up_meta

    # This is a method to get mapping id for given flavor.
    def _get_mapping_id(self, anilist_id, flavor):

        try:
            # Get mapping id from database if it exists else raise KeyError.
            mapping_id = database.get_show(anilist_id)[flavor]
            if not mapping_id:
                raise KeyError
        except:
            # Call method to get flavor id using armkai API.
            mapping_id = self._get_flavor_id(anilist_id, flavor)

        # Return the mapping id.
        return mapping_id

    # This is a method to get flavor id using armkai API.
    def _get_flavor_id(self, anilist_id, flavor):

        # Call armkai API to get response based on type of id provided.
        arm_resp = database.get(client.request, 4, 'https://armkai.vercel.app/api/search?type=anilist&id={0}'.format(anilist_id))
        arm_resp = json.loads(arm_resp)

        # Extract flavor-specific id from the response.
        flavor_id = arm_resp.get(flavor[:-3])

        # Return the flavor id.
        return flavor_id

    # This is a method to get mapping id for given flavor using MAL id. 
    def _get_mapping_id_mal(self, mal_id, flavor):

        try:
            # Get mapping id from database if it exists else raise KeyError.
            mapping_id = database.get_show_mal(mal_id)[flavor]
            if not mapping_id:
                raise KeyError
        except:
            # Call method to get flavor id using armkai API.
            mapping_id = self._get_flavor_id_mal(mal_id, flavor)

        # Return the mapping id.
        return mapping_id

    # This is a method to get flavor id using armkai API for MAL id.
    def _get_flavor_id_mal(self, mal_id, flavor):

        # Call armkai API to get response based on type of id provided.
        arm_resp = database.get(client.request, 4, 'https://armkai.vercel.app/api/search?type=mal&id={0}'.format(mal_id))
        arm_resp = json.loads(arm_resp)

        # Extract flavor-specific id from the response.
        flavor_id = arm_resp.get(flavor[:-3])

        # Return the flavor id.
        return flavor_id

    # This is a method to format login data into dictionary.
    def _format_login_data(self, name, image, token):

        # Define dictionary to store login data.
        login_data = {
            "name": name,
            "image": image,
            "token": token,
        }

        # Return the login data.
        return login_data

    # This is a method to parse the view metadata.
    def _parse_view(self, base, is_dir=True):

        # Create list with an item in it containing metadata of the show.
        return [
            utils.allocate_item(
                "%s" % base["name"],
                base["url"],
                is_dir,
                base["image"],
                base["plot"],
                base.get("fanart"),
                base.get("poster"),
                landscape=base.get("landscape"),
                banner=base.get("banner"),
                clearart=base.get("clearart"),
                clearlogo=base.get("clearlogo"),
            )
        ]

    # This is a method to change the URL string according to given url.
    def _to_url(self, url=''):
        if url.startswith("/"):
            url = url[1:]
        return "%s/%s" % (self._URL, url)

    # These are methods to make requests using the client class.
    def _get_request(self, url, headers=None, cookies=None, data=None, params=None):
        return client.request(url, headers=headers, cookie=cookies, post=data, params=params)

    def _post_request(self, url, headers=None, cookies=None, params=None, json=None):
        return client.request(url, headers=headers, cookie=cookies, post=json, jpost=True, params=params)

    def _patch_request(self, url, headers=None, cookies=None, params=None, json=None):
        return client.request(url, headers=headers, cookie=cookies, post=json, jpost=True, params=params, method='PATCH')

    def _put_request(self, url, headers=None, cookies=None, data=None, params=None):
        return client.request(url, headers=headers, cookie=cookies, post=data, params=params, method='PUT')

    def _delete_request(self, url, headers=None, cookies=None, params=None):
        return client.request(url, headers=headers, cookie=cookies, params=params, method='DELETE')
