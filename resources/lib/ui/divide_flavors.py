# -*- coding: utf-8 -*-
import json
import requests

from resources.lib.ui.globals import g

def div_flavor(f):
    def wrapper(*args, **kwargs):
        if g.get_setting("general.divflavors") == "true":
            mal_dub = _get_mal_dub()

            return f(dub=mal_dub, *args, **kwargs)

        return f(*args, **kwargs)

    return wrapper

def _get_mal_dub():
    try:
        mal_dub = open(g.MAL_DUB_FILE_PATH, 'r+')
        mal_dub = json.load(mal_dub)
    except:
        file_to_dump = open(g.MAL_DUB_FILE_PATH, 'a+')
        mal_dub = requests.get('https://armkai.vercel.app/api/maldub').json()
        json.dump(mal_dub, file_to_dump, indent=4)

    return mal_dub