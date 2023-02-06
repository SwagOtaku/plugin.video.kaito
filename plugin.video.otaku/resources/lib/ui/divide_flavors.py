import json
from resources.lib.ui import control, client


def div_flavor(f):
    def wrapper(*args, **kwargs):
        if control.getSetting("General.divflavors") == "true":
            mal_dub = _get_mal_dub()

            return f(dub=mal_dub, *args, **kwargs)

        return f(*args, **kwargs)

    return wrapper


def _get_mal_dub():
    try:
        mal_dub = open(control.maldubFile, 'r+')
        mal_dub = json.load(mal_dub)
    except:
        file_to_dump = open(control.maldubFile, 'a+')
        mal_dub_raw = client.request('https://raw.githubusercontent.com/MAL-Dubs/MAL-Dubs/main/data/dubInfo.json')
        mal_dub_list = json.loads(mal_dub_raw)["dubbed"]
        mal_dub = {}
        for item in mal_dub_list:
            mal_dub[str(item)] = {"dub": True}
        json.dump(mal_dub, file_to_dump, indent=4)

    return mal_dub
