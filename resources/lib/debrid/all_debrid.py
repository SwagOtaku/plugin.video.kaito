# -*- coding: utf-8 -*-
from future import standard_library
standard_library.install_aliases()
from builtins import object
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from urllib.parse import urljoin
import re

from resources.lib.ui import source_utils
from resources.lib.ui import control
from resources.lib.ui.globals import g

def alldebird_guard_response(func):
    def wrapper(*args, **kwarg):
        try:
            response = func(*args, **kwarg)
            if response.status_code in [200, 201]:
                return response

            if response.status_code == 429:
##                tools.log('Alldebrid Throttling Applied, Sleeping for {} seconds'.format(1), '')
##                tools.kodi.sleep(1 * 1000)
                control.kodi.sleep(1 * 1000)
                response = func(*args, **kwarg)

##            tools.log('AllDebrid returned a {} ({}): while requesting {}'.format(response.status_code,
##                                                                                 AllDebrid.http_codes[
##                                                                                     response.status_code],
##                                                                                 response.url), 'warning')
            return None
        except requests.exceptions.ConnectionError:
            return None
        except not requests.exceptions.ConnectionError:
##            tools.showDialog.ok(tools.addonName, "Somethign wnet wrong with AllDebrid cancelling action")
            return None

    return wrapper


class AllDebrid(object):
    session = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    base_url = 'https://api.alldebrid.com/v4/'

    http_codes = {
        200: 'Success',
        400: 'Bad Request, The request was unacceptable, often due to missing a required parameter',
        401: 'Unauthorized',
        404: 'Not Found, Api endpoint doesn\'t exist',
        500: 'Internal Server Error',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
        504: 'Gateway Timeout',
    }

    def __init__(self):
        self.agent_identifier = 'test'
        self.apikey = g.get_setting('alldebrid.apikey')

    @alldebird_guard_response
    def get(self, url, **params):
##        if not tools.getSetting('alldebrid.enabled') == 'true':
##            return
        params.update({'agent': self.agent_identifier})
        return self.session.get(urljoin(self.base_url, url), params=params)

    def get_json(self, url, **params):
        return self._extract_data(self.get(url, **params).json())

    @alldebird_guard_response
    def post(self, url, post_data=None, **params):
##        if not tools.getSetting('alldebrid.enabled') == 'true' or self.apikey == '':
##            return
        params.update({'agent': self.agent_identifier})
        return self.session.post(urljoin(self.base_url, url), data=post_data, params=params)

    def post_json(self, url, post_data=None, **params):
        post_ = self.post(url, post_data, **params)
        if not post_:
            return
        return self._extract_data(post_.json())

    @staticmethod
    def _extract_data(response):
        if 'data' in response:
            return response['data']
        else:
            return response

    def auth(self):
        resp = self.get_json('pin/get')
        expiry = pin_ttl = int(resp['expires_in'])
        auth_complete = False
        control.copy2clip(resp['pin'])
        control.progressDialog.create(
            g.ADDON_NAME + ': AllDebrid Auth',
            control.create_multiline_message(
                line1=g.lang(30100).format(
                    g.color_string(resp['base_url'])
                ),
                line2=g.lang(30101).format(
                    g.color_string(resp['pin'])
                ),
                line3=g.lang(30102),
            ),
        )

        # Seems the All Debrid servers need some time do something with the pin before polling
        # Polling to early will cause an invalid pin error
        control.kodi.sleep(5 * 1000)
        control.progressDialog.update(100)
        while not auth_complete and not expiry <= 0 and not control.progressDialog.iscanceled():
            auth_complete, expiry = self.poll_auth(check=resp['check'], pin=resp['pin'])
            progress_percent = 100 - int((float(pin_ttl - expiry) / pin_ttl) * 100)
            control.progressDialog.update(progress_percent)
            control.kodi.sleep(1 * 1000)
        try:
            control.progressDialog.close()
        except:
            pass

        self.store_user_info()

        if auth_complete:
            control.ok_dialog(g.ADDON_NAME, 'AllDebrid {}'.format(g.lang(30103)))
        else:
            return

    def poll_auth(self, **params):
        resp = self.get_json('pin/check', **params)
        if resp['activated']:
            g.set_setting('alldebrid.apikey', resp['apikey'])
            self.apikey = resp['apikey']
            return True, 0

        return False, int(resp['expires_in'])

    def store_user_info(self):
        user_information = self.get_json('user', apikey=self.apikey)
        if user_information is not None:
            g.set_setting('alldebrid.username', user_information['user']['username'])

    def check_hash(self, hash_list):
        return self.post_json('magnet/instant', {'magnets[]': hash_list}, apikey=self.apikey)

    def upload_magnet(self, magnet_hash):
        return self.get_json('magnet/upload', apikey=self.apikey, magnets=magnet_hash)

    def update_relevant_hosters(self):
        return
##        return database.get(self.get_json, 1, 'hosts')

    def get_hosters(self, hosters):
        host_list = self.update_relevant_hosters()
        if host_list is not None:
            hosters['premium']['all_debrid'] = \
                [(d, d.split('.')[0])
                 for l in list(host_list['hosts'].values())
                 if 'status' in l and l['status']
                 for d in l['domains']]
        else:
            import traceback
            traceback.print_exc()
            hosters['premium']['all_debrid'] = []

    def resolve_hoster(self, url):
        resolve = self.get_json('link/unlock', apikey=self.apikey, link=url)
        return resolve['link']

    def magnet_status(self, magnet_id):
        return self.get_json('magnet/status', apikey=self.apikey, id=magnet_id)

    def resolve_single_magnet(self, hash_, magnet, episode=''):
        selected_file = None

        magnet_id = self.upload_magnet(magnet)['magnets'][0]['id']
        folder_details = self.magnet_status(magnet_id)['magnets']['links']

        folder_details = [{'link': l['link'], 'path': l['filename']} for l in folder_details]

        if episode:
            selected_file = source_utils.get_best_match('path', folder_details, episode)
            self.delete_magnet(magnet_id)
            if selected_file is not None:
                return self.resolve_hoster(selected_file['link'])

        selected_file = folder_details[0]['link']

        if selected_file is None:
            return

        self.delete_magnet(magnet_id)
        return self.resolve_hoster(selected_file)

    def delete_magnet(self, magnet_id):
        return self.get_json('magnet/delete', apikey=self.apikey, id=magnet_id)