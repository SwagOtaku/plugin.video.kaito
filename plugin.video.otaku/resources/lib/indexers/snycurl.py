import json

from resources.lib.ui import client


class SyncUrl:
    BaseURL = 'https://find-my-anime.dtimur.de/api'

    def get_anime_data(self, anime_id, anime_id_provider):
        params = {
            'id': anime_id,
            'provider': anime_id_provider
        }
        r = client.request(self.BaseURL, params=params)
        if r:
            res = json.loads(r)
            return res
