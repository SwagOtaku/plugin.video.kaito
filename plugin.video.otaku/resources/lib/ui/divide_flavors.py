import json
from resources.lib.ui import control, client


def div_flavor(f):
    def wrapper(*args, **kwargs):
        if control.getSetting("divflavors.bool") == "true":
            dubsub_filter = control.getSetting("divflavors.menu")
            mal_dub = _get_mal_dub()

            return f(dub=mal_dub, dubsub_filter=dubsub_filter, *args, **kwargs)

        return f(*args, **kwargs)

    return wrapper


def _get_mal_dub():
    try:
        with open(control.maldubFile, 'r+') as mal_dub:
            mal_dub = json.load(mal_dub)
    except:
        with open(control.maldubFile, 'a+') as file_to_dump:
            mal_dub_raw = client.request('https://raw.githubusercontent.com/MAL-Dubs/MAL-Dubs/main/data/dubInfo.json')
            mal_dub_list = json.loads(mal_dub_raw)["dubbed"]
            mal_dub = {str(item): {'dub': True} for item in mal_dub_list}
            json.dump(mal_dub, file_to_dump, indent=4)

    return mal_dub
