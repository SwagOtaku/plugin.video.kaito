import json

from resources.lib.ui import client


def get_all_anime(mal_id):
    # Chiaki refers to this call as "Get Watch Order"
    url = 'https://chiaki.vercel.app/get?group_id=%s' % (mal_id)

    r = client.request(url)
    if r:
        r = json.loads(r)
    return r