from resources.lib.ui import client, database
import json
import threading


class TMDBAPI:
    def __init__(self):
        self.apiKey = "6974ec27debf5cce1218136e2a36f64b"
        self.baseUrl = "https://api.themoviedb.org/3/"
        self.posterPath = "https://image.tmdb.org/t/p/w500"
        self.thumbPath = "https://image.tmdb.org/t/p/w500"
        self.backgroundPath = "https://image.tmdb.org/t/p/original"
        self.art = {}
        self.request_response = None
        self.threads = []

    def get_request(self, url):
        if '?' not in url:
            url += "?"
        else:
            url += "&"

        if 'api_key' not in url:
            url += "api_key=%s" % self.apiKey
            url = self.baseUrl + url

        response = client.request(url)
        if not response:
            response = client.request(url, verify=False)

        if response:
            response = json.loads(response)
            self.request_response = response
            return response
        else:
            return None

    def get_TMDB_Fanart_Threaded(self, tmdb_url, fanart_args):

        self.threads.append(threading.Thread(target=self.get_request, args=(tmdb_url,)))

        for thread in self.threads:
            thread.start()

        for thread in self.threads:
            thread.join()

    def showFanart(self, traktItem):

        try:
            if traktItem['tmdb'] is None:
                return None

            url = 'tv/%s?append_to_response=images&language=en-US' % \
                  traktItem['tmdb']

            self.get_TMDB_Fanart_Threaded(url, (traktItem['tvdb'], 'tv'))

            details = self.request_response

            if details is None:
                return details

            try:
                self.art['fanart'] = self.backgroundPath + str(details.get('backdrop_path', ''))
            except:
                pass

            item = self.art

        except:
            import traceback
            traceback.print_exc()
            return None

        return item

    def showPoster(self, traktItem):

        try:
            if traktItem['tmdb'] is None:
                return None

            url = 'tv/%s?append_to_response=images&language=en-US' % \
                  traktItem['tmdb']

            self.get_TMDB_Fanart_Threaded(url, (traktItem['tvdb'], 'tv'))

            details = self.request_response

            if details is None:
                return details

            try:
                self.art['poster'] = self.posterPath + str(details.get('poster_path', ''))
            except:
                pass

            item = self.art

        except:
            import traceback
            traceback.print_exc()
            return None

        return item

    def showSeasonToListItem(self, seasonObject=None, showArgs=None):

        try:
            url = 'tv/%s/season/%s?append_to_response=images&language=en-US' % (
                str(showArgs['tmdb']), str(seasonObject))

            self.get_TMDB_Fanart_Threaded(url, (83121, 'season'))

            details = self.request_response

            if details is None:
                return None

            try:
                self.art['poster'] = self.posterPath + str(details.get('poster_path', ''))
                self.art['thumb'] = self.posterPath + str(details.get('poster_path', ''))
            except:
                pass

            item = self.art

        except:
            import traceback
            traceback.print_exc()
            return None

        return item

    def episodeIDToListItem(self, season=None, number=None, showArgs=None):
        if showArgs['tmdb'] is None:
            return None

        url = 'tv/%s/season/%s?language=en-US' % (
            showArgs['tmdb'],
            season)
        response = database.get(self.get_request, 1, url)

        if response:
            ep = [x for x in response.get('episodes') if x.get('episode_number') == number][0]
            self.art['landscape'] = self.backgroundPath + ep.get('still_path', '')
            self.art['thumb'] = self.thumbPath + ep.get('still_path', '')

        item = self.art

        return item

    def parseEpisodeInfo(self, response, traktInfo, showArgs):
        try:
            if "status_code" in response:
                if response["status_code"] == 34:
                    return None

            art = {}

            try:
                art['landscape'] = self.backgroundPath + response.get('still_path', '')
                art['thumb'] = self.thumbPath + response.get('still_path', '')
            except:
                pass

        except:
            import traceback
            traceback.print_exc()
            return None

        return art

    def getArt(self, meta_ids, mtype):
        art = {}
        mid = meta_ids.get('themoviedb') or meta_ids.get('tmdb')
        if mid is None:
            tvdb = meta_ids.get('thetvdb') or meta_ids.get('tvdb')
            if tvdb:
                url = 'find/{0}?external_source=tvdb_id'.format(tvdb)
                res = self.get_request(url)
                res = res.get('tv_results')
                if res:
                    mid = res[0].get('id')

        if mid:
            url = '{0}/{1}/images?include_image_language=en,ja,null'.format(mtype[0:5], mid)
            res = self.get_request(url)
            if res:
                if res.get('backdrops'):
                    items = []
                    items2 = []
                    for item in res.get('backdrops'):
                        if item.get('file_path'):
                            items.append(self.backgroundPath + item.get('file_path'))
                            items.append(self.thumbPath + item.get('file_path'))
                    art.update({'fanart': items, 'thumb': items2})

                if res.get('logos'):
                    items = []
                    for item in res.get('logos'):
                        if item.get('url'):
                            items.append(self.backgroundPath + item.get('url'))
                    art.update({'clearart': items})

        return art
