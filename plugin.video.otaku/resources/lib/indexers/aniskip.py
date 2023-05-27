import json

from resources.lib.ui import client


def get_skip_times(mal_id, episodenum, skip_type):
    # skip_types = op, recap, mixed-ed, mixed-op, ed

    url = 'https://api.aniskip.com/v2/skip-times/%s/%s' % (mal_id, episodenum)
    params = {
        'types': skip_type,
        'episodeLength': 0
    }

    r = client.request(url, params=params)
    if r:
        r = json.loads(r)
    return r
