# Import necessary libraries/modules
import copy
import itertools
import json
import pickle
import re
import threading
from functools import partial

# Import external libraries/modules
import six
from bs4 import BeautifulSoup, SoupStrainer

# Import internal modules
from resources.lib.debrid import (all_debrid, debrid_link, premiumize,
                                  real_debrid)
from resources.lib.ui import control, database, source_utils, utils
from resources.lib.ui.BrowserBase import BrowserBase
from six.moves import filter, urllib_parse


# Define class sources, inheriting from BrowserBase class
class sources(BrowserBase):
    # Set _BASE_URL attribute based on user preferences
    _BASE_URL = 'https://nyaa.si/' if control.getSetting('provider.nyaa') == 'true' else 'https://nyaa.iss.ink/'

    # Define private method for parsing anime view
    def _parse_anime_view(self, res):
        # Create empty dictionary to store info
        info = {}
        # Create url variable by formatting result hash and debrid_provider
        url = '{}/{}'.format(res['debrid_provider'], res['hash'])
        # Create name variable from result name
        name = res['name']
        # Set default image
        image = 'DefaultVideo.png'
        # Add title and mediatype to info dictionary
        info['title'] = name
        info['mediatype'] = 'tvshow'
        # Return allocated item with url, image, and info dictionary
        return utils.allocate_item(name, "play_latest/" + str(url), False, image, info)

    # Define private method for parsing nyaa episode view
    def _parse_nyaa_episode_view(self, res, episode):
        # Create dictionary with necessary information
        source = {
            'release_title': res['name'].encode('utf-8') if six.PY2 else res['name'],
            'hash': res['hash'],
            'type': 'torrent',
            'quality': self.get_quality(res['name']),
            'debrid_provider': res['debrid_provider'],
            'provider': 'nyaa',
            'episode_re': episode,
            'size': res['size'],
            'info': source_utils.getInfo(res['name']),
            'lang': source_utils.getAudio_lang(res['name'])
        }

        return source

    # Define private method for parsing nyaa cached episode view
    def _parse_nyaa_cached_episode_view(self, res, episode):
        # Create dictionary with necessary information
        source = {
            'release_title': res['name'].encode('utf-8') if six.PY2 else res['name'],
            'hash': res['hash'],
            'type': 'torrent',
            'quality': self.get_quality(res['name']),
            'debrid_provider': res['debrid_provider'],
            'provider': 'nyaa (Local Cache)',
            'episode_re': episode,
            'size': res['size'],
            'info': source_utils.getInfo(res['name']),
            'lang': source_utils.getAudio_lang(res['name'])
        }

        return source

    # Define method to get quality based on release title
    def get_quality(self, release_title):
        # Convert release title to lowercase
        release_title = release_title.lower()
        # Set default quality
        quality = 'NA'
        # Check for different qualities in release title and update quality accordingly
        if '4k' in release_title:
            quality = '4K'
        if '2160' in release_title:
            quality = '4K'
        if '1080' in release_title:
            quality = '1080p'
        if '720' in release_title:
            quality = '720p'
        if '480' in release_title:
            quality = 'NA'

        return quality

    # Define method to handle paging
    def _handle_paging(self, total_pages, base_url, page):
        # Check if on last page and return empty list if true
        if page == total_pages:
            return []
        # Set next page variable
        next_page = page + 1
        # Use next_page variable to create name variable
        name = "Next Page (%d/%d)" % (next_page, total_pages)
        # Return allocated item with base_url and fanart
        return [utils.allocate_item(name, base_url % next_page, True, 'next.png', fanart='next.png')]

    # Define private method for making JSON request
    def _json_request(self, url, data=''):
        # Load response as JSON and return
        response = json.loads(self._get_request(url, data))
        return response

    # Define method for processing anime view
    def _process_anime_view(self, url, data, base_plugin_url, page):
        # Make JSON request
        json_resp = self._get_request(url)
        # Parse results using BeautifulSoup
        results = BeautifulSoup(json_resp, 'html.parser')
        rex = r'(magnet:)+[^"]*'
        search_results = [
            (i.find_all('a', {'href': re.compile(rex)})[0].get('href'),
             i.find_all('a', {'class': None})[1].get('title'))
            for i in results.select("tr.default,tr.success")
        ]

        list_ = [
            {'magnet': magnet,
             'name': name
             }
            for magnet, name in search_results]

        for torrent in list_:
            torrent['hash'] = re.findall(r'btih:(.*?)(?:&|$)', torrent['magnet'])[0]

        cache_list = TorrentCacheCheck().torrentCacheCheck(list_)
        all_results = list(map(self._parse_anime_view, cache_list))

        return all_results

    # Define function with parameters url, episode, and season (with None as default value)
    def _process_nyaa_episodes(self, url, episode, season=None):
        # Make GET request and parse results using BeautifulSoup
        html = self._get_request(url)
        mlink = SoupStrainer('div', {'class': 'table-responsive'})
        soup = BeautifulSoup(html, "html.parser", parse_only=mlink)
        rex = r'(magnet:)+[^"]*'
        # Create a list comprehension to extract desired data from the parsed HTML
        list_ = [
            {'magnet': i.find('a', {'href': re.compile(rex)}).get('href'),
             'name': i.find_all('a', {'class': None})[1].get('title'),
             'size': i.find_all('td', {'class': 'text-center'})[1].text.replace('i', ''),
             'downloads': int(i.find_all('td', {'class': 'text-center'})[-1].text)}
            for i in soup.select("tr.danger,tr.default,tr.success")
        ]
        # Define two regular expressions
        regex = r'\ss(\d+)|season\s(\d+)|(\d+)+(?:st|[nr]d|th)\sseason'
        regex_ep = r'\de(\d+)\b|\se(\d+)\b|\s-\s(\d{1,3})\b'
        rex = re.compile(regex)
        rex_ep = re.compile(regex_ep)

        # Create an empty list to store filtered data
        filtered_list = []

        # Loop through each item in the list and filter by season and episode number if applicable
        for idx, torrent in enumerate(list_):
            # Add hash to dict by finding it in the magnet link
            torrent['hash'] = re.findall(r'btih:(.*?)(?:&|$)', torrent['magnet'])[0]

            # If season is specified, filter by season and episode number
            if season:
                title = torrent['name'].lower()

                ep_match = rex_ep.findall(title)
                ep_match = list(map(int, list(filter(None, itertools.chain(*ep_match)))))

                if ep_match and ep_match[0] != int(episode):
                    regex_ep_range = r'\s\d+-\d+|\s\d+~\d+|\s\d+\s-\s\d+|\s\d+\s~\s\d+'
                    rex_ep_range = re.compile(regex_ep_range)

                    if rex_ep_range.search(title):
                        pass
                    else:
                        continue

                match = rex.findall(title)
                match = list(map(int, list(filter(None, itertools.chain(*match)))))

                if not match or match[0] == int(season):
                    filtered_list.append(torrent)

            # Otherwise, add all items to filtered list
            else:
                filtered_list.append(torrent)

        # Call TorrentCacheCheck() method and sort the list by number of downloads
        cache_list = TorrentCacheCheck().torrentCacheCheck(filtered_list)
        cache_list = sorted(cache_list, key=lambda k: k['downloads'], reverse=True)

        # Use map function to call _parse_nyaa_episode_view() for each item in the list and return all results
        mapfunc = partial(self._parse_nyaa_episode_view, episode=episode)
        all_results = list(map(mapfunc, cache_list))
        return all_results

    # This function processes nyaa backup
    def _process_nyaa_backup(self, url, anilist_id, _zfill, episode='', rescrape=False):
        # Making a request to get json response
        json_resp = self._get_request(url)
        # Using BeautifulSoup to parse html
        results = BeautifulSoup(json_resp, 'html.parser')
        # Regular expression pattern to find magnet links
        rex = r'(magnet:)+[^"]*'
        # List comprehension to select required information from search results
        search_results = [
            (i.find_all('a', {'href': re.compile(rex)})[0].get('href'),
             i.find_all('a', {'class': None})[1].get('title'),
             i.find_all('td', {'class': 'text-center'})[1].text,
             i.find_all('td', {'class': 'text-center'})[-1].text)
            for i in results.select("tr.danger,tr.default,tr.success")
        ][:30]
        # Comprehension to create list of torrent dictionaries with required information
        list_ = [
            {'magnet': magnet,
             'name': name,
             'size': size.replace('i', ''),
             'downloads': int(downloads)
             }
            for magnet, name, size, downloads in search_results]
        # Adding hash key to the dictionary by using regular expression to fetch hash value
        for torrent in list_:
            torrent['hash'] = re.findall(r'btih:(.*?)(?:&|$)', torrent['magnet'])[0]

        # Adding torrent list to database if not rescraping
        if not rescrape:
            database.addTorrentList(anilist_id, list_, _zfill)

        # Checking torrent cache and sorting by downloads in descending order
        cache_list = TorrentCacheCheck().torrentCacheCheck(list_)
        cache_list = sorted(cache_list, key=lambda k: k['downloads'], reverse=True)

        # Mapping function to parse results
        mapfunc = partial(self._parse_nyaa_episode_view, episode=episode)
        all_results = list(map(mapfunc, cache_list))
        return all_results

    # This function processes nyaa movie
    def _process_nyaa_movie(self, url, episode):
        # Making a request to get json response
        json_resp = self._get_request(url)
        # Using BeautifulSoup to parse html
        results = BeautifulSoup(json_resp, 'html.parser')
        # Regular expression pattern to find magnet links
        rex = r'(magnet:)+[^"]*'
        # List comprehension to select required information from search results
        search_results = [
            (i.find_all('a', {'href': re.compile(rex)})[0].get('href'),
             i.find_all('a', {'class': None})[1].get('title'),
             i.find_all('td', {'class': 'text-center'})[1].text,
             i.find_all('td', {'class': 'text-center'})[-1].text)
            for i in results.select("tr.danger,tr.default,tr.success")
        ]
        # Comprehension to create list of torrent dictionaries with required information
        list_ = [
            {'magnet': magnet,
             'name': name,
             'size': size.replace('i', ''),
             'downloads': int(downloads)
             }
            for magnet, name, size, downloads in search_results]

        # Adding hash key to the dictionary by using regular expression to fetch hash value
        for idx, torrent in enumerate(list_):
            torrent['hash'] = re.findall(r'btih:(.*?)(?:&|$)', torrent['magnet'])[0]

        # Checking torrent cache and sorting by downloads in descending order
        cache_list = TorrentCacheCheck().torrentCacheCheck(list_)
        cache_list = sorted(cache_list, key=lambda k: k['downloads'], reverse=True)

        # Mapping function to parse results
        mapfunc = partial(self._parse_nyaa_episode_view, episode=episode)
        all_results = list(map(mapfunc, cache_list))
        return all_results

    # This function processes cached sources
    def _process_cached_sources(self, list_, episode):
        # Checking torrent cache
        cache_list = TorrentCacheCheck().torrentCacheCheck(list_)
        # Mapping function to parse results
        mapfunc = partial(self._parse_nyaa_cached_episode_view, episode=episode)
        all_results = list(map(mapfunc, cache_list))
        return all_results

    # This function gets the latest anime by scraping web page
    def get_latest(self, page=1):
        url = self._BASE_URL + '?f=0&c=1_0&q='
        data = ''
        return self._process_anime_view(url, data, "latest/%d", page)

    # This function gets the latest dubbed anime by scraping web page
    def get_latest_dub(self, page=1):
        url = self._BASE_URL + '?f=0&c=1_2&q=english+dub'
        data = ''
        return self._process_anime_view(url, data, "latest_dub/%d", page)

    # Defines the function storeTorrentResults which takes in a parameter torrent_list
    def storeTorrentResults(self, torrent_list):

        try:
            # checks if the length of the torrent list is 0
            if len(torrent_list) == 0:
                return

            # adds torrent list information to the database
            database.addTorrent(self.item_information, torrent_list)
        except:
            pass

    # Defines the function get_sources which takes in several parameters: query, anilist_id, episode, status, media_type, and rescrape
    def get_sources(self, query, anilist_id, episode, status, media_type, rescrape):
        # cleans the title of the query
        query = self._clean_title(query)
        # checks if media type is "movie", returns movie sources if true
        if media_type == 'movie':
            return self._get_movie_sources(query, anilist_id, episode)

        # gets episode sources by calling _get_episode_sources function
        sources = self._get_episode_sources(query, anilist_id, episode, status, rescrape)

        # if there are no sources and ":" exists in the query
        if not sources and ':' in query:
            q1, q2 = query.split('|')
            q1 = q1[1:-1].split(':')[0]
            q2 = q2[1:-1].split(':')[0]
            query2 = '({0})|({1})'.format(q1, q2)
            sources = self._get_episode_sources(query2, anilist_id, episode, status, rescrape)

        # if there are still no sources
        if not sources:
            sources = self._get_episode_sources_backup(query, anilist_id, episode)

        # returns the sources
        return sources

    # Defines the function _get_episode_sources which takes in several parameters: show, anilist_id, episode, status, and rescrape
    def _get_episode_sources(self, show, anilist_id, episode, status, rescrape):
        # if rescrape is true, calls _get_episode_sources_pack function
        if rescrape:
            return self._get_episode_sources_pack(show, anilist_id, episode)

        try:
            # retrieves cached torrent list from database
            cached_sources, zfill_int = database.getTorrentList(anilist_id)
            if cached_sources:
                return self._process_cached_sources(cached_sources, episode.zfill(zfill_int))
        except ValueError:
            pass

        # creates query string by combining show and episode (padded with 0s)
        query = '%s "- %s"' % (show, episode.zfill(2))

        # gets season information from database
        season = database.get_season_list(anilist_id)
        if season:
            # pads season number with 0s
            season = str(season['season']).zfill(2)
            # adds season information to query string
            query += '|"S%sE%s "' % (season, episode.zfill(2))

        # creates URL for Nyaa.si search
        url = '%s?f=0&c=1_0&q=%s&s=downloads&o=desc' % (self._BASE_URL, urllib_parse.quote_plus(query))

        # if status is "FINISHED", updates the query and URL string
        if status == 'FINISHED':
            query = '%s "Batch"|"Complete Series"' % (show)

            episodes = pickle.loads(database.get_show(anilist_id)['kodi_meta'])['episodes']
            if episodes:
                query += '|"01-{0}"|"01~{0}"|"01 - {0}"|"01 ~ {0}"'.format(episodes)

            if season:
                query += '|"S{0}"|"Season {0}"'.format(season)
                query += '|"S%sE%s "' % (season, episode.zfill(2))

            query += '|"- %s"' % (episode.zfill(2))

            url = '%s?f=0&c=1_0&q=%s&s=seeders&&o=desc' % (self._BASE_URL, urllib_parse.quote_plus(query))

        # processes and returns the Nyaa.si episode sources
        return self._process_nyaa_episodes(url, episode.zfill(2), season)

    # Defines the function _get_episode_sources_backup which takes in several parameters: db_query, anilist_id, and episode
    def _get_episode_sources_backup(self, db_query, anilist_id, episode):
        # retrieves show information from Firebase database
        show = self._get_request('https://kaito-title.firebaseio.com/%s.json' % anilist_id)
        show = json.loads(show)

        # if there is no show information, returns empty list
        if not show:
            return []

        # If general_title exists in show
        if 'general_title' in show:
            query = show['general_title'].encode('utf-8') if six.PY2 else show['general_title']
            _zfill = show.get('zfill', 2)
            episode = episode.zfill(_zfill)
            query = urllib_parse.quote_plus(query)
            url = '%s?f=0&c=1_0&q=%s&s=downloads&o=desc' % (self._BASE_URL, query)
            return self._process_nyaa_backup(url, anilist_id, _zfill, episode)

        try:
            # retrieves kodi_meta information from database and updates it with the query
            kodi_meta = pickle.loads(database.get_show(anilist_id)['kodi_meta'])
            kodi_meta['query'] = db_query + '|{}'.format(show['general_title'])
            database.update_kodi_meta(anilist_id, kodi_meta)
        except:
            pass

        # creates query string by combining show information and episode (padded with 0s)
        query = '%s "- %s"' % (show.encode('utf-8') if six.PY2 else show, episode.zfill(2))
        season = database.get_season_list(anilist_id)
        if season:
            # pads season number with 0s
            season = str(season['season']).zfill(2)
            # adds season information to query string
            query += '|"S%sE%s"' % (season, episode.zfill(2))

        # creates URL for Nyaa.si search
        url = '%s?f=0&c=1_0&q=%s' % (self._BASE_URL, urllib_parse.quote_plus(query))
        # processes and returns the Nyaa.si episode sources
        return self._process_nyaa_episodes(url, episode)

    # Defines the function _get_episode_sources_pack which takes in several parameters: show, anilist_id, and episode
    def _get_episode_sources_pack(self, show, anilist_id, episode):
        # creates query string for Nyaa.si search
        query = '%s "Batch"|"Complete Series"' % (show)

        episodes = pickle.loads(database.get_show(anilist_id)['kodi_meta'])['episodes']
        if episodes:
            query += '|"01-{0}"|"01~{0}"|"01 - {0}"|"01 ~ {0}"'.format(episodes)

        season = database.get_season_list(anilist_id)
        if season:
            season = season['season']
            query += '|"S{0}"|"Season {0}"'.format(season)

        # creates URL for Nyaa.si search
        url = '%s?f=0&c=1_2&q=%s&s=seeders&&o=desc' % (self._BASE_URL, urllib_parse.quote_plus(query))
        # processes and returns the Nyaa.si episode sources
        return self._process_nyaa_backup(url, anilist_id, 2, episode.zfill(2), True)

    # Definition of '_get_movie_sources' function
    def _get_movie_sources(self, query, anilist_id, episode):
        query = urllib_parse.quote_plus(query)
        url = '%s?f=0&c=1_2&q=%s&s=downloads&o=desc' % (self._BASE_URL, query)
        sources = self._process_nyaa_movie(url, '1')

        if not sources:
            sources = self._get_movie_sources_backup(anilist_id)

        return sources

    # Definition of '_get_movie_sources_backup' function
    def _get_movie_sources_backup(self, anilist_id, episode='1'):
        # Get data from 'https://kimetsu-title.firebaseio.com/%s.json' URL
        show = self._get_request("https://kimetsu-title.firebaseio.com/%s.json" % anilist_id)
        show = json.loads(show)
        if not show:
            return []

        if 'general_title' in show:
            # get query based on 'general_title' key
            query = show['general_title']
            query = urllib_parse.quote_plus(query)
            url = '%s?f=0&c=1_2&q=%s&s=downloads&o=desc' % (self._BASE_URL, query)
            return self._process_nyaa_backup(url, episode)

        query = urllib_parse.quote_plus(show)
        # set URL based on query
        url = '%s?f=0&c=1_2&q=%s' % (self._BASE_URL, query)
        return self._process_nyaa_movie(url, episode)


# Class definition for TorrentCacheCheck
class TorrentCacheCheck:
    def __init__(self):
        self.premiumizeCached = []
        self.realdebridCached = []
        self.all_debridCached = []
        self.debrid_linkCached = []
        self.threads = []

        self.episodeStrings = None
        self.seasonStrings = None

    # Definition of 'torrentCacheCheck' function
    def torrentCacheCheck(self, torrent_list):
        if control.real_debrid_enabled():
            self.threads.append(
                threading.Thread(target=self.real_debrid_worker, args=(copy.deepcopy(torrent_list),)))

        if control.debrid_link_enabled():
            self.threads.append(
                threading.Thread(target=self.debrid_link_worker, args=(copy.deepcopy(torrent_list),)))

        if control.premiumize_enabled():
            self.threads.append(threading.Thread(target=self.premiumize_worker, args=(copy.deepcopy(torrent_list),)))

        if control.all_debrid_enabled():
            self.threads.append(
                threading.Thread(target=self.all_debrid_worker, args=(copy.deepcopy(torrent_list),)))

        # starting all the threads
        for i in self.threads:
            i.start()
        # joining all the threads
        for i in self.threads:
            i.join()

        cachedList = self.realdebridCached + self.premiumizeCached + self.all_debridCached + self.debrid_linkCached
        return cachedList

    # Function to check cache on 'all_debrid'
    def all_debrid_worker(self, torrent_list):

        api = all_debrid.AllDebrid()

        if len(torrent_list) == 0:
            return

        cache_check = api.check_hash([i['hash'] for i in torrent_list])
        if not cache_check:
            return

        cache_list = []
        cached_items = [m.get('hash') for m in cache_check if m.get('instant') is True]

        for i in torrent_list:
            if i['hash'] in cached_items:
                i['debrid_provider'] = 'all_debrid'
                cache_list.append(i)

        self.all_debridCached = cache_list

    # Function to check cache on 'debrid_link'
    def debrid_link_worker(self, torrent_list):

        api = debrid_link.DebridLink()

        if len(torrent_list) == 0:
            return

        cache_check = api.check_hash([i['hash'] for i in torrent_list])

        if not cache_check:
            return

        cache_list = []

        for i in torrent_list:
            if i['hash'] in list(cache_check.keys()):
                i['debrid_provider'] = 'debrid_link'
                cache_list.append(i)

        self.debrid_linkCached = cache_list

    # Function to check cache on 'real_debrid'
    def real_debrid_worker(self, torrent_list):
        cache_list = []

        hash_list = [i['hash'] for i in torrent_list]

        if len(hash_list) == 0:
            return
        api = real_debrid.RealDebrid()
        realDebridCache = api.checkHash(hash_list)

        for i in torrent_list:
            try:
                if 'rd' not in realDebridCache.get(i['hash'], {}):
                    continue
                if len(realDebridCache[i['hash']]['rd']) >= 1:
                    i['debrid_provider'] = 'real_debrid'
                    cache_list.append(i)
                else:
                    pass
            except KeyError:
                pass

        self.realdebridCached = cache_list

    # Function to check cache on 'premiumize'
    def premiumize_worker(self, torrent_list):
        hash_list = [i['hash'] for i in torrent_list]
        if len(hash_list) == 0:
            return
        premiumizeCache = premiumize.Premiumize().hash_check(hash_list)
        premiumizeCache = premiumizeCache['response']
        cache_list = []
        count = 0
        for i in torrent_list:
            if premiumizeCache[count] is True:
                i['debrid_provider'] = 'premiumize'
                cache_list.append(i)
            count += 1

        self.premiumizeCached = cache_list
