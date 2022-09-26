from resources.lib.ui import client
import json


class FANARTAPI:
    def __init__(self):
        self.apiKey = "dfe6380e34f49f9b2b9518184922b49c"
        self.baseUrl = "https://webservice.fanart.tv/v3"

    def get_request(self, url):
        headers = {'Api-Key': self.apiKey}
        response = client.request(url, headers=headers)
        if response:
            response = json.loads(response)
            return response
        else:
            return None

    def getArt(self, meta_ids, mtype):
        art = {}
        mid = meta_ids.get('tmdb') if mtype == 'movies' else meta_ids.get('tvdb')
        if mid:
            url = '{0}/{1}/{2}'.format(self.baseUrl, mtype, mid)
            res = self.get_request(url)
            if res:
                if mtype == 'movies':
                    if res.get('moviebackground'):
                        if len(res.get('moviebackground')) > 1:
                            for item in res.get('moviebackground'):
                                if item.get('lang') == 'en' or item.get('lang') == '':
                                    art.update({'fanart': item.get('url')})
                                    break
                        else:
                            art.update({'fanart': res.get('moviebackground')[0].get('url')})
                    if res.get('moviethumb'):
                        if len(res.get('moviethumb')) > 1:
                            for item in res.get('moviethumb'):
                                if item.get('lang') == 'en' or item.get('lang') == '':
                                    art.update({'thumb': item.get('url')})
                                    break
                        else:
                            art.update({'thumb': res.get('moviethumb')[0].get('url')})
                else:
                    if res.get('showbackground'):
                        if len(res.get('showbackground')) > 1:
                            for item in res.get('showbackground'):
                                if item.get('lang') == 'en' or item.get('lang') == '':
                                    art.update({'fanart': item.get('url')})
                                    break
                        else:
                            art.update({'fanart': res.get('showbackground')[0].get('url')})
                    if res.get('tvthumb'):
                        if len(res.get('tvthumb')) > 1:
                            for item in res.get('tvthumb'):
                                if item.get('lang') == 'en' or item.get('lang') == '':
                                    art.update({'thumb': item.get('url')})
                                    break
                        else:
                            art.update({'thumb': res.get('tvthumb')[0].get('url')})
        return art
