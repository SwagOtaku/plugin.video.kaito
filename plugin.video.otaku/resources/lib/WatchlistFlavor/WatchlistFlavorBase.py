import pickle
from resources.lib.ui import utils, database, client, control
import json


class WatchlistFlavorBase(object):
    _URL = None
    _TITLE = None
    _NAME = None
    _IMAGE = None

    def __init__(self, auth_var=None, username=None, password=None, user_id=None, token=None, refresh=None, sort=None, title_lang=None):
        if type(self) is WatchlistFlavorBase:
            raise Exception("Base Class should not be created")

        self._auth_var = auth_var
        self._username = username
        self._password = password
        self._user_id = user_id
        self._token = token
        self._refresh = refresh
        self._sort = sort
        if title_lang:
            self._title_lang = title_lang
        else:
            self._title_lang = self._get_title_lang(control.getSetting("titlelanguage"))

    def _get_title_lang(self, title_key):
        title_lang = {
            "40370": "userPreferred",
            "Romaji (Shingeki no Kyojin)": "userPreferred",
            "40371": "english",
            "English (Attack on Titan)": "english"
        }
        return title_lang[title_key]

    @classmethod
    def name(cls):
        if cls._NAME is None:
            raise Exception("Missing Name")

        return cls._NAME

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

    @property
    def flavor_name(self):
        return self._NAME

    @property
    def username(self):
        return self._username

    def login(self):
        raise NotImplementedError("login should be implemented by subclass")

    def watchlist(self):
        raise NotImplementedError("watchlist should be implemented by subclass")

    def get_watchlist_status(self, status):
        raise NotImplementedError("get_watchlist_status should be implemented by subclass")

    def watchlist_update(self, episode, kitsu_id):
        raise NotImplementedError("watchlist_update should be implemented by subclass")

    def _get_next_up_meta(self, mal_id, next_up, anilist_id=None):
        next_up_meta = {}

        if anilist_id:
            show = database.get_show(anilist_id)
        else:
            show = database.get_show_mal(mal_id)

        if show:
            show_meta = pickle.loads(show['kodi_meta'])
            next_up_meta['image'] = show_meta.get('fanart')
            anilist_id = show['anilist_id']
            episodes = database.get_episode_list(show['anilist_id'])
            if episodes:
                try:
                    episode_meta = pickle.loads(episodes[next_up]['kodi_meta'])
                    next_up_meta['title'] = episode_meta['info']['title']
                    next_up_meta['image'] = episode_meta['image']['thumb']
                    next_up_meta['plot'] = episode_meta['info']['plot']
                except:
                    pass

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

        return anilist_id, next_up_meta

    def _get_mapping_id(self, anilist_id, flavor):
        try:
            mapping_id = database.get_show(anilist_id)[flavor]
            if not mapping_id:
                raise KeyError
        except:
            mapping_id = self._get_flavor_id(anilist_id, flavor)

        return mapping_id

    def _get_flavor_id(self, anilist_id, flavor):
        arm_resp = database.get(client.request, 4, 'https://armkai.vercel.app/api/search?type=anilist&id={0}'.format(anilist_id))
        arm_resp = json.loads(arm_resp)
        flavor_id = arm_resp.get(flavor[:-3])
        return flavor_id

    def _format_login_data(self, name, image, token):
        login_data = {
            "name": name,
            "image": image,
            "token": token,
        }

        return login_data

    def _parse_view(self, base, is_dir=True):
        return [
            utils.allocate_item("%s" % base["name"],
                                base["url"],
                                is_dir,
                                base["image"],
                                base["plot"],
                                base.get("fanart"),
                                base.get("poster"))
        ]

    def _to_url(self, url=''):
        if url.startswith("/"):
            url = url[1:]
        return "%s/%s" % (self._URL, url)

    def _get_request(self, url, headers=None, cookies=None, data=None, params=None):
        return client.request(url, headers=headers, cookie=cookies, post=data, params=params)

    def _post_request(self, url, headers=None, cookies=None, params=None, json=None):
        return client.request(url, headers=headers, cookie=cookies, post=json, jpost=True, params=params)

    def _patch_request(self, url, headers=None, cookies=None, params=None, json=None):
        return client.request(url, headers=headers, cookie=cookies, post=json, jpost=True, params=params, method='PATCH')

    def _put_request(self, url, headers=None, cookies=None, data=None, params=None):
        return client.request(url, headers=headers, cookie=cookies, post=data, params=params, method='PUT')
