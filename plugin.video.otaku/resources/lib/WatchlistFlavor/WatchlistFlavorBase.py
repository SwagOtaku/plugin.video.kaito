import json
import pickle
import random

from resources.lib.ui import client, control, database, utils


class WatchlistFlavorBase:
    _URL = None
    _TITLE = None
    _NAME = None
    _IMAGE = None

    def __init__(self, auth_var=None, username=None, password=None, user_id=None, token=None, refresh=None, sort=None, title_lang=None):
        self._auth_var = auth_var
        self._username = username
        self._password = password
        self._user_id = user_id
        self._token = token
        self._refresh = refresh
        self._sort = sort
        self._title_lang = title_lang if title_lang else control.title_lang(control.getSetting("general.titlelanguage"))

    @classmethod
    def name(cls):
        return cls._NAME

    @property
    def image(self):
        return self._IMAGE

    @property
    def title(self):
        return self._TITLE

    @property
    def url(self):
        return self._URL

    @property
    def flavor_name(self):
        return self._NAME

    @property
    def username(self):
        return self._username

    @staticmethod
    def _get_next_up_meta(mal_id, next_up, anilist_id=''):
        next_up_meta = {}
        show = database.get_show(anilist_id) if anilist_id else database.get_show_mal(mal_id)

        if show:
            anilist_id = show['anilist_id']
            show_meta = database.get_show_meta(anilist_id)

            if show_meta:
                art = pickle.loads(show_meta.get('art'))
                if art.get('fanart'):
                    next_up_meta['image'] = random.choice(art.get('fanart'))

            episodes = database.get_episode_list(show['anilist_id'])
            if episodes:
                try:
                    episode_meta = pickle.loads(episodes[next_up]['kodi_meta'])
                except IndexError:
                    episode_meta = None
                if episode_meta:
                    if control.getSetting('interface.cleantitles') == 'false':
                        next_up_meta['title'] = episode_meta['info']['title']
                        next_up_meta['plot'] = episode_meta['info']['plot']
                    else:
                        next_up_meta['title'] = 'Episode {0}'.format(episode_meta["info"]["episode"])
                    next_up_meta['image'] = episode_meta['image']['thumb']
                    next_up_meta['aired'] = episode_meta['info'].get('aired')

        return anilist_id, next_up_meta, show

    def _get_mapping_id(self, anilist_id, flavor):
        show = database.get_show(anilist_id)
        mapping_id = show[flavor] if show and show.get(flavor) else self._get_flavor_id(anilist_id, flavor)
        return mapping_id

    @staticmethod
    def _get_flavor_id(anilist_id, flavor):
        params = {
            'type': "anilist",
            "id": anilist_id
        }
        r = database.get(client.request, 4, 'https://armkai.vercel.app/api/search', params=params)
        res = json.loads(r)
        flavor_id = res.get(flavor[:-3])
        database.add_mapping_id(anilist_id, flavor, flavor_id)
        return flavor_id

    @staticmethod
    def _parse_view(base, is_dir=True):
        return [
            utils.allocate_item(
                "%s" % base["name"],
                base["url"],
                is_dir,
                base["image"],
                base["info"],
                base.get("fanart"),
                base.get("poster"),
                landscape=base.get("landscape"),
                banner=base.get("banner"),
                clearart=base.get("clearart"),
                clearlogo=base.get("clearlogo"),
            )
        ]

    def _get_request(self, url, headers=None, cookies=None, data=None, params=None):
        return client.request(url, headers=headers, cookie=cookies, post=data, params=params)

    def _post_request(self, url, headers=None, cookies=None, params=None, json=None):
        return client.request(url, headers=headers, cookie=cookies, post=json, jpost=True, params=params, error=True)

    def _patch_request(self, url, headers=None, cookies=None, params=None, json=None):
        return client.request(url, headers=headers, cookie=cookies, post=json, jpost=True, params=params, method='PATCH')

    def _put_request(self, url, headers=None, cookies=None, data=None, params=None):
        return client.request(url, headers=headers, cookie=cookies, post=data, params=params, method='PUT')

    def _delete_request(self, url, headers=None, cookies=None, params=None):
        return client.request(url, headers=headers, cookie=cookies, params=params, method='DELETE')
