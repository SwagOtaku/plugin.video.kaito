import json

from resources.lib.ui import client


def get_watch_order_list(mal_id):
    # Chiaki refers to this call as "Get Watch Order"
    url = 'https://chiaki.vercel.app/get'

    r = client.request(url, params={'group_id': mal_id})
    if r:
        r = json.loads(r)
    return r
