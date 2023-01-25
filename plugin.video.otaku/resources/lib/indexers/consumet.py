import json
import pickle

from functools import partial
from resources.lib.ui import client, database, utils


class CONSUMETAPI:
    def __init__(self):
        self.baseUrl = 'https://api.consumet.org/'
        self.episodesUrl = 'meta/anilist/episodes/{0}?provider={1}'
        self.streamUrl = 'anime/{0}/watch/{1}'

    def _json_request(self, url):
        url = self.baseUrl + url
        response = database.get(
            client.request,
            4,
            url
        )
        if response:
            response = json.loads(response)
        return response

    def _parse_episode_view(self, res, show_id, show_meta, poster, fanart, eps_watched, update_time):
        url = "%s/%s/" % (show_id, res['number'])
        name = 'Ep. %d (%s)' % (res['number'], res.get('title', ''))
        image = res.get('image')

        info = {}
        info['plot'] = res.get('description', '')
        info['title'] = res.get('title', '')
        # info['season'] = int(season)
        info['episode'] = res['number']
        try:
            if int(eps_watched) >= res['number']:
                info['playcount'] = 1
        except:
            pass
        info['aired'] = res.get('airDate')[:10] if res.get('airDate') else ''

        info['tvshowtitle'] = pickle.loads(database.get_show(show_id)['kodi_meta'])['title_userPreferred']
        info['mediatype'] = 'episode'
        parsed = utils.allocate_item(name, "play/" + str(url), False, image, info, fanart, poster)
        database._update_episode(show_id, number=res['number'], update_time=update_time, kodi_meta=parsed, air_date=info['aired'])
        return parsed

    def _process_episode_view(self, anilist_id, show_meta, poster, fanart, eps_watched):
        from datetime import date
        update_time = date.today().isoformat()
        all_results = []
        result = self.get_anilist_meta(anilist_id)
        if result:
            result = result.get('episodes')
            mapfunc = partial(self._parse_episode_view, show_id=anilist_id, show_meta=show_meta, poster=poster, fanart=fanart, eps_watched=eps_watched, update_time=update_time)
            all_results = list(map(mapfunc, result))
        return all_results

    def _parse_episodes(self, res, show_id, eps_watched):
        parsed = pickle.loads(res['kodi_meta'])

        try:
            if int(eps_watched) >= res['number']:
                parsed['info']['playcount'] = 1
        except:
            pass

        return parsed

    def _process_episodes(self, anilist_id, episodes, eps_watched):
        mapfunc = partial(self._parse_episodes, show_id=anilist_id, eps_watched=eps_watched)
        all_results = list(map(mapfunc, episodes))

        return all_results

    def get_anilist_meta(self, anilist_id):
        url = 'meta/anilist/info/{0}'.format(anilist_id)
        return self._json_request(url)

    def get_episodes(self, anilist_id, filter_lang):
        show_meta = database.get_show_meta(anilist_id)
        meta_ids = pickle.loads(show_meta.get('meta_ids'))
        kodi_meta = pickle.loads(database.get_show(anilist_id).get('kodi_meta'))
        kodi_meta.update(pickle.loads(show_meta.get('art')))
        fanart = kodi_meta.get('fanart')
        poster = kodi_meta.get('poster')
        eps_watched = kodi_meta.get('eps_watched')
        episodes = database.get_episode_list(int(anilist_id))

        if episodes:
            return (self._process_episodes(anilist_id, episodes, eps_watched), 'episodes')

        return (self._process_episode_view(anilist_id, meta_ids, poster, fanart, eps_watched), 'episodes')

    def get_sources(self, anilist_id, episode, provider, lang=None):
        sources = []
        episodes = self._json_request(self.episodesUrl.format(anilist_id, provider))
        if episodes:
            if episodes[0].get('number') != 1:
                episode = episodes[0].get('number') - 1 + int(episode)
            episode_id = [x.get('id') for x in episodes if x.get('number') == int(episode)][0]

            sources = self._json_request(self.streamUrl.format(provider, episode_id))

        return sources

    def get_size(self, size=0):
        power = 1024.0
        n = 0
        power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB'}
        while size > power:
            size /= power
            n += 1
        return '{0:.2f} {1}'.format(size, power_labels[n])
