import json
import pickle
import re
from functools import partial

from resources.lib.indexers.fanart import FANARTAPI
from resources.lib.indexers.tmdb import TMDBAPI
from resources.lib.ui import client, database, utils
from six.moves import urllib_parse


class ENIMEAPI:
    def __init__(self):
        self.baseUrl = 'https://api.enime.moe/'
        self.art = {}
        self.request_response = None

    def _json_request(self, url):
        url = self.baseUrl + url
        response = client.request(url)
        if response:
            response = json.loads(response)
        return response

    def get_anilist_mapping(self, anilist_id):
        url = 'mapping/anilist/{0}'.format(anilist_id)
        return self._json_request(url)
