import json

from resources.lib.ui import client, database


class SyncUrl:
    BaseURL = 'https://find-my-anime.dtimur.de/api'

    def get_anime_data(self, anime_id, anime_id_provider):
        params = {
            'id': anime_id,
            'provider': anime_id_provider,
            'includeAdult': 'true'
        }
        r = database.get(client.request, 2, self.BaseURL, params=params)
        if r:
            res = json.loads(r)
            return res
