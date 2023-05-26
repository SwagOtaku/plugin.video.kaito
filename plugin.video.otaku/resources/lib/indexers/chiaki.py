import json

from resources.lib.ui import client


def get_all_anime(mal_id, title, info, mal_url):
    # Gives you all related anime with one Mal ID

    url = 'https://chiaki.vercel.app/get?group_id=%s' % (mal_id)
    params = {
        'number': 0,
        'name': title,
        'info': info,
        'url': mal_url
    }

    r = client.request(url, params=params)
    if r:
        r = json.loads(r)
    return r
