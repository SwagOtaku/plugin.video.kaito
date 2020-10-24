import threading
from . import nyaa, gogoanime, animixplay
from ..ui import control
from resources.lib.windows.get_sources_window import GetSources as DisplayWindow
import time

class CancelProcess(Exception):
    pass


def getSourcesHelper(actionArgs):
##    sources_window = Sources(*SkinManager().confirm_skin_path('get_sources.xml'),
##                             actionArgs=actionArgs)

    sources_window = Sources(*('get_sources.xml', control.ADDON_PATH),
                             actionArgs=actionArgs)

    sources = sources_window.doModal()
    try:
        del sources_window
    except:
        pass
    return sources

class Sources(DisplayWindow):
    def __init__(self, xml_file, location, actionArgs=None):
        try:
            super(Sources, self).__init__(xml_file, location, actionArgs)
        except:
            self.args = actionArgs
            self.canceled = False

        self.torrent_threads = []
        self.hoster_threads = []
        self.torrentProviders = []
        self.hosterProviders = []
        self.language = 'en'
        self.torrentCacheSources = []
        self.embedSources = []
        self.hosterSources = []
        self.cloud_files = []
        self.remainingProviders = ['nyaa', 'gogo', 'animixplay']
        self.allTorrents = {}
        self.allTorrents_len = 0
        self.hosterDomains = {}
        self.torrents_qual_len = [0, 0, 0, 0]
        self.hosters_qual_len = [0, 0, 0, 0]
        self.trakt_id = ''
        self.silent = False
        self.return_data = (None, None, None)
        self.basic_windows = True
        self.progress = 1
        self.duplicates_amount = 0
        self.domain_list = []
        self.display_style = 0
        self.background_dialog = None
        self.running_providers = []

        self.line1 = ''
        self.line2 = ''
        self.line3 = ''

        self.host_domains = []
        self.host_names = []

        self.remainingSources = ['1', '2', '3']
        self.nyaaSources = []
        self.gogoSources = []
        self.animixplaySources = []
        self.threads = []

    def getSources(self, args):
        query = args['query']
        anilist_id = args['anilist_id']
        episode = args['episode']
        media_type = args['media_type']
        rescrape = args['rescrape']
        get_backup = args['get_backup']
        self.setProperty('process_started', 'true')

        if control.real_debrid_enabled() or control.all_debrid_enabled() or control.premiumize_enabled():
            self.threads.append(
                threading.Thread(target=self.nyaa_worker, args=(query, anilist_id, episode, media_type, rescrape,)))
        else:
            self.remainingProviders.remove('nyaa')

        self.threads.append(
            threading.Thread(target=self.gogo_worker, args=(anilist_id, episode, get_backup, rescrape,)))

        self.threads.append(
            threading.Thread(target=self.animixplay_worker, args=(anilist_id, episode, get_backup, rescrape,)))

        for i in self.threads:
            i.start()

        timeout = 20
        start_time = time.time()
        runtime = 0

        while self.progress < 100:
            if (len(self.remainingProviders) == 0 and runtime > 5):
                break

            if self.canceled:
                break

            try:
                self.updateProgress()
            except:
                pass

            try:
                self.setProgress()
                self.setText("4K: %s | 1080: %s | 720: %s | SD: %s" % (
                    control.colorString(self.torrents_qual_len[0] + self.hosters_qual_len[0]),
                    control.colorString(self.torrents_qual_len[1] + self.hosters_qual_len[1]),
                    control.colorString(self.torrents_qual_len[2] + self.hosters_qual_len[2]),
                    control.colorString(self.torrents_qual_len[3] + self.hosters_qual_len[3]),
                ))

            except:
                import traceback
                traceback.print_exc()

            # Update Progress
            time.sleep(.200)
            runtime = time.time() - start_time
            self.progress = int(100 - float(1 - (runtime / float(timeout))) * 100)
    
        if len(self.torrentCacheSources) + len(self.embedSources) == 0:
            self.return_data = []
            self.close()
            return

        sourcesList = self.sortSources(self.torrentCacheSources, self.embedSources)
        self.return_data = sourcesList
        self.close()
        return

    def nyaa_worker(self, query, anilist_id, episode, media_type, rescrape):
        self.nyaaSources = nyaa.sources().get_sources(query, anilist_id, episode, media_type, rescrape)
        self.torrentCacheSources += self.nyaaSources
        self.remainingProviders.remove('nyaa')        

    def gogo_worker(self, anilist_id, episode, get_backup, rescrape):
        if not rescrape:
            self.gogoSources = gogoanime.sources().get_sources(anilist_id, episode, get_backup)
            self.embedSources += self.gogoSources

        self.remainingProviders.remove('gogo')        

    def animixplay_worker(self, anilist_id, episode, get_backup, rescrape):
        if not rescrape:
            self.animixplaySources = animixplay.sources().get_sources(anilist_id, episode, get_backup)
            self.embedSources += self.animixplaySources

        self.remainingProviders.remove('animixplay')

    def resolutionList(self):
        resolutions = []
##        max_res = 0
        max_res = int(control.getSetting('general.maxResolution'))
        if max_res == 3 or max_res < 3:
            resolutions.append('NA')
        if max_res < 3:
            resolutions.append('720p')
        if max_res < 2:
            resolutions.append('1080p')
        if max_res < 1:
            resolutions.append('4K')

        return resolutions

    def debrid_priority(self):
        p = []

        if control.getSetting('premiumize.enabled') == 'true':
            p.append({'slug': 'premiumize', 'priority': int(control.getSetting('premiumize.priority'))})
        if control.getSetting('realdebrid.enabled') == 'true':
            p.append({'slug': 'real_debrid', 'priority': int(control.getSetting('rd.priority'))})
        if control.getSetting('alldebrid.enabled') == 'true':
            p.append({'slug': 'all_debrid', 'priority': int(control.getSetting('alldebrid.priority'))})

        p = sorted(p, key=lambda i: i['priority'])

        return p

    def sortSources(self, torrent_list, embed_list):
##        sort_method = 0
        sort_method = int(control.getSetting('general.sortsources'))

        sortedList = []
##
        resolutions = self.resolutionList()

        resolutions.reverse()

        if control.getSetting('general.dubsort') == 'true':
            _torrent_list = torrent_list
            torrent_list = [i for i in _torrent_list if i['lang'] > 0] + \
                           [i for i in embed_list if i['lang'] > 0]

            embed_list = [i for i in _torrent_list if i['lang'] == 0] + \
                         [i for i in embed_list if i['lang'] == 0]

        debrid_priorities = self.debrid_priority()

        for resolution in resolutions:
            if sort_method == 0 or sort_method == 2:
                for debrid in debrid_priorities:
                    for torrent in torrent_list:
                        if debrid['slug'] == torrent['debrid_provider']:
                            if torrent['quality'] == resolution:
                                sortedList.append(torrent)

            if sort_method == 1 or sort_method == 2:
                for file in embed_list:
                    if file['quality'] == resolution:
                        sortedList.append(file)

        if sort_method == 1:
            for resolution in resolutions:
                for debrid in debrid_priorities:
                    for torrent in torrent_list:
                        if torrent['debrid_provider'] == debrid['slug']:
                            if torrent['quality'] == resolution:
                                sortedList.append(torrent)

        if sort_method == 0:
            for resolution in resolutions:
                for file in embed_list:
                    if file['quality'] == resolution:
                        sortedList.append(file)

        if control.getSetting('general.disable265') == 'true':
            sortedList = [i for i in sortedList if 'HEVC' not in i['info']]

        if control.getSetting('general.hidedub') == 'true':
            sortedList = [i for i in sortedList if i['lang'] != 2]

        return sortedList

    def colorNumber(self, number):

        if int(number) > 0:
            return control.colorString(number, 'green')
        else:
            return control.colorString(number, 'red')

    def updateProgress(self):

        list1 = [
                len([i for i in self.nyaaSources if i['quality'] == '4K']),
                len([i for i in self.nyaaSources if i['quality'] == '1080p']),
                len([i for i in self.nyaaSources if i['quality'] == '720p']),
                len([i for i in self.nyaaSources if i['quality'] == 'NA']),
            ]

        self.torrents_qual_len = list1

        list2 = [
                len([i for i in self.embedSources if i['quality'] == '4K']),
                len([i for i in self.embedSources if i['quality'] == '1080p']),
                len([i for i in self.embedSources if i['quality'] == '720p']),
                len([i for i in self.embedSources if i['quality'] == 'NA']),
            ]

        self.hosters_qual_len = list2

        return
