import requests
import json
import threading


class TMDBAPI:
    def __init__(self):
        self.apiKey = "6974ec27debf5cce1218136e2a36f64b"
        self.baseUrl = "https://api.themoviedb.org/3/"
        self.posterPath = "https://image.tmdb.org/t/p/w500"
        self.thumbPath = "https://image.tmdb.org/t/p/w500"
        self.backgroundPath = "https://image.tmdb.org/t/p/w1280"
        self.art = {}
        self.request_response = None
        self.threads = []

    def get_request(self, url):
        try:
            if '?' not in url:
                url += "?"
            else:
                url += "&"

            if 'api_key' not in url:
                url += "api_key=%s" % self.apiKey
                url = self.baseUrl + url

            try:
                try:
                    response = requests.get(url)
                except requests.exceptions.SSLError:
                    response = requests.get(url, verify=False)
            except requests.exceptions.ConnectionError:
                return

            if '200' in str(response):
                response = json.loads(response.text)
                self.request_response = response
                return response
            # This code is now deprecated as the throttling has been removed,
            # We will leave it here though in case they decide to use it later
            # elif 'Retry-After' in response.headers:
            #     # API REQUESTS ARE BEING THROTTLED, INTRODUCE WAIT TIME
            #     throttleTime = response.headers['Retry-After']
            #     tools.log('TMDB Throttling Applied, Sleeping for %s seconds' % throttleTime, '')
            #     sleep(int(throttleTime) + 1)
            #     return self.get_request(url)
            else:
                return None
        except:
            import traceback
            traceback.print_exc()

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

            url = 'tv/%s?&append_to_response=credits,alternative_titles,videos,content_ratings,images&language=en-US' % \
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

            url = 'tv/%s?&append_to_response=credits,alternative_titles,videos,content_ratings,images&language=en-US' % \
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
            url = 'tv/%s/season/%s?&append_to_response=credits,videos,images&language=en-US' % (
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
        try:
            if showArgs['tmdb'] is None:
                return None

            url = 'tv/%s/season/%s/episode/%s?&append_to_response=credits,videos,images&language=en-US' % (
                showArgs['tmdb'],
                season,
                number)
            response = self.get_request(url)

            if response.get('status_code') == 34:
                return None

            try:
                self.art['landscape'] = self.backgroundPath + response.get('still_path', '')
                self.art['thumb'] = self.thumbPath + response.get('still_path', '')
            except:
                pass

            item = self.art

            return item
        except:
            return None

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
