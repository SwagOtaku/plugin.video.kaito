# -*- coding: utf-8 -*-

import sys

from kodi_six import xbmc
from resources.lib.debrid import (all_debrid, debrid_link, premiumize,
                                  real_debrid)
from resources.lib.ui import control
from resources.lib.windows.base_window import BaseWindow

try:
    sysaddon = sys.argv[0]
    syshandle = int(sys.argv[1])
except:
    # Running outside Kodi Call
    pass

sys.path.append(control.dataPath)


class Resolver(BaseWindow):

    def __init__(self, xml_file, location=None, actionArgs=None):
        try:
            super(Resolver, self).__init__(xml_file, location, actionArgs=actionArgs)
        except:
            pass
        self.return_data = None
        self.canceled = False
        self.progress = 1
        self.silent = False

        self.pack_select = None
        self.resolvers = {'all_debrid': all_debrid.AllDebrid,
                          'debrid_link': debrid_link.DebridLink,
                          'premiumize': premiumize.Premiumize,
                          'real_debrid': real_debrid.RealDebrid}

    def onInit(self):
        self.resolve(self.sources, self.args, self.pack_select)

    def resolve(self, sources, args, pack_select=False):
        try:

            stream_link = None
            loop_count = 0
            # Begin resolving links

            for i in sources:
                debrid_provider = i.get('debrid_provider', 'None').replace('_', ' ')
                loop_count += 1
                try:
                    if self.is_canceled():
                        self.close()
                        return

                    self.setProperty('release_title', str(i['release_title']))
                    self.setProperty('debrid_provider', debrid_provider)
                    self.setProperty('source_provider', i['provider'])
                    self.setProperty('source_resolution', i['quality'])
                    self.setProperty('source_info', " ".join(i['info']))
                    self.setProperty('source_type', i['type'])

                    if i['type'] == 'torrent':
                        stream_link = self.resolve_source(self.resolvers[i['debrid_provider']], i)
                        if stream_link is None:
                            continue
                        else:
                            self.return_data = stream_link
                            self.close()
                            return

                    elif i['type'] == 'cloud' or i['type'] == 'hoster':

                        if i['type'] == 'cloud' and i['debrid_provider'] == 'premiumize':
                            stream_link = i['hash']
                        else:
                            stream_link = self.resolve_source(self.resolvers[i['debrid_provider']], i)

                        if stream_link is None:
                            continue
                        else:
                            self.return_data = stream_link
                            self.close()
                            return

                    elif i['type'] == 'direct':
                        stream_link = i['hash']
                        xbmc.sleep(200)

                        if stream_link is None:
                            continue
                        else:
                            self.return_data = stream_link
                            if i.get('subs'):
                                self.return_data = (stream_link, i.get('subs'))
                            self.close()
                            return

                    elif i['type'] == 'embed':
                        from resources.lib.ui import embed_extractor
                        stream_link = embed_extractor.load_video_from_url(i['hash'])

                        if stream_link is None:
                            continue
                        else:
                            self.return_data = stream_link
                            self.close()
                            return

                except:
                    import traceback
                    traceback.print_exc()
                    continue

            self.close()
            return
        except:
            import traceback
            traceback.print_exc()
            self.close()
            return

    def resolve_source(self, api, source):
        stream_link = None
        api = api()
        hash_ = source['hash']
        magnet = 'magnet:?xt=urn:btih:' + hash_
        try:

            if source['type'] == 'torrent':
                stream_link = api.resolve_single_magnet(hash_, magnet, source['episode_re'])
            elif source['type'] == 'cloud' or source['type'] == 'hoster':
                stream_link = api.resolve_hoster(hash_)
        except:
            import traceback
            traceback.print_exc()
            pass
        return stream_link

    def doModal(self, sources, args, pack_select):

        # if tools.getSetting('general.tempSilent') == 'true':
        #     self.silent = True

        if not sources:
            return None

        self.sources = sources
        self.args = args
        self.pack_select = pack_select
        self.setProperty('release_title', str(self.sources[0]['release_title']))
        self.setProperty('debrid_provider', self.sources[0].get('debrid_provider', 'None').replace('_', ' '))
        self.setProperty('source_provider', self.sources[0]['provider'])
        self.setProperty('source_resolution', self.sources[0]['quality'])
        self.setProperty('source_info', " ".join(self.sources[0]['info']))
        self.setProperty('source_type', self.sources[0]['type'])
        self.setProperty('source_size', self.sources[0]['size'])

        # if 'size' in self.sources[0]:
        #     self.setProperty('source_size', control.source_size_display(self.sources[0]['size']))

        if not self.silent:
            super(Resolver, self).doModal()
        else:
            self.resolve(sources, args, pack_select)

        if not self.canceled:
            return self.return_data
        else:
            return None

    def is_canceled(self):
        if not self.silent:
            if self.canceled:
                return True

    def onAction(self, action):

        id = action.getId()
        if id == 92 or id == 10:
            self.canceled = True
            self.close()

    def setBackground(self, url):
        if not self.silent:
            self.background.setImage(url)
        pass

    def close(self):
        if not self.silent:
            control.dialogWindow.close(self)
