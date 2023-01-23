import json

from resources.lib.ui import client


class FANARTAPI:
    def __init__(self):
        self.apiKey = "dfe6380e34f49f9b2b9518184922b49c"
        self.baseUrl = "https://webservice.fanart.tv/v3"
        self.lang = ['en', 'ja', '']

    def get_request(self, url):
        headers = {'Api-Key': self.apiKey}
        response = client.request(url, headers=headers)
        if response:
            response = json.loads(response)
            return response
        else:
            return None

    def getArt(self, meta_ids, mtype='tv'):
        art = {}
        if mtype == 'movies':
            mid = meta_ids.get('themoviedb') or meta_ids.get('tmdb')
        else:
            mid = meta_ids.get('thetvdb') or meta_ids.get('tvdb')

        if mid:
            url = '{0}/{1}/{2}'.format(self.baseUrl, mtype, mid)
            res = self.get_request(url)
            if res:
                if mtype == 'movies':
                    if res.get('moviebackground'):
                        items = []
                        for item in res.get('moviebackground'):
                            if item.get('lang') in self.lang:
                                items.append(item.get('url'))
                        art.update({'fanart': items})
                    if res.get('moviethumb'):
                        items = []
                        for item in res.get('moviethumb'):
                            if item.get('lang') in self.lang:
                                items.append(item.get('url'))
                        art.update({'thumb': items})
                else:
                    if res.get('showbackground'):
                        items = []
                        for item in res.get('showbackground'):
                            if item.get('lang') in self.lang:
                                items.append(item.get('url'))
                        art.update({'fanart': items})
                    if res.get('tvthumb'):
                        items = []
                        for item in res.get('tvthumb'):
                            if item.get('lang') in self.lang:
                                items.append(item.get('url'))
                        art.update({'thumb': items})

                if res.get('clearart'):
                    items = []
                    for item in res.get('clearart'):
                        if item.get('lang') in self.lang:
                            items.append(item.get('url'))
                    art.update({'clearart': items})
                elif res.get('hdclearart'):
                    items = []
                    for item in res.get('hdclearart'):
                        if item.get('lang') in self.lang:
                            items.append(item.get('url'))
                    art.update({'clearart': items})
                elif res.get('hdmovieclearart'):
                    items = []
                    for item in res.get('hdmovieclearart'):
                        if item.get('lang') in self.lang:
                            items.append(item.get('url'))
                    art.update({'clearart': items})

                if res.get('clearlogo'):
                    items = []
                    for item in res.get('clearlogo'):
                        if item.get('lang') in self.lang:
                            items.append(item.get('url'))
                    art.update({'clearlogo': items})
                elif res.get('hdtvlogo'):
                    items = []
                    for item in res.get('hdtvlogo'):
                        if item.get('lang') in self.lang:
                            items.append(item.get('url'))
                    art.update({'clearlogo': items})
                elif res.get('hdmovielogo'):
                    items = []
                    for item in res.get('hdmovielogo'):
                        if item.get('lang') in self.lang:
                            items.append(item.get('url'))
                    art.update({'clearlogo': items})

        return art
