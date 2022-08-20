# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

import re
import os
import threading
import sys
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcvfs
import xbmcgui

from resources.lib.ui import control


class GlobalVariables(object):
    CONTENT_FOLDER = "files"
    CONTENT_MOVIE = "movies"
    CONTENT_SHOW = "tvshows"
    CONTENT_SEASON = "seasons"
    CONTENT_EPISODE = "episodes"
    CONTENT_GENRES = "genres"
    CONTENT_YEARS = "years"
    MEDIA_FOLDER = "file"
    MEDIA_MOVIE = "movie"
    MEDIA_SHOW = "tvshow"
    MEDIA_SEASON = "season"
    MEDIA_EPISODE = "episode"

    DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
    DATE_TIME_FORMAT_ZULU = DATE_TIME_FORMAT + ".000Z"
    DATE_FORMAT = "%Y-%m-%d"

    PYTHON3 = control.PYTHON3
    UNICODE = control.unicode
    SEMVER_REGEX = re.compile(r"^((?:\d+\.){2}\d+)")

    def __init__(self):
        self.IS_ADDON_FIRSTRUN = None
        self.ADDON = None
        self.ADDON_DATA_PATH = None
        self.ADDON_ID = None
        self.ADDON_NAME = None
        self.VERSION = None
        self.CLEAN_VERSION = None
        self.USER_AGENT = None
        self.DEFAULT_FANART = None
        self.DEFAULT_ICON = None
        self.ADDON_USERDATA_PATH = None
        self.SETTINGS_CACHE = {}
        self.LANGUAGE_CACHE = {}
        self.PLAYLIST = None
        self.HOME_WINDOW = None
        self.KODI_FULL_VERSION = None
        self.KODI_VERSION = None
        self.PLATFORM = self._get_system_platform()
        self.URL = None
        self.PLUGIN_HANDLE = 0
        self.IS_SERVICE = True
        self.BASE_URL = None
        self.PATH = None
        self.PARAM_STRING = None
        self.REQUEST_PARAMS = None
        self.FROM_WIDGET = False
        self.PAGE = 1

    def __del__(self):
        self.deinit()

    def deinit(self):
        self.ADDON = None
        del self.ADDON
        self.PLAYLIST = None
        del self.PLAYLIST
        self.HOME_WINDOW = None
        del self.HOME_WINDOW

    def init_globals(self, argv=None, addon_id=None):
        self.IS_ADDON_FIRSTRUN = self.IS_ADDON_FIRSTRUN is None
        self.SETTINGS_CACHE = {}
        self.LANGUAGE_CACHE = {}
        self.ADDON = xbmcaddon.Addon()
        self.ADDON_ID = addon_id if addon_id else self.ADDON.getAddonInfo("id")
        self.ADDON_NAME = self.ADDON.getAddonInfo("name")
        self.VERSION = self.ADDON.getAddonInfo("version")
        self.CLEAN_VERSION = self.SEMVER_REGEX.findall(self.VERSION)[0]
        self.USER_AGENT = "{} - {}".format(self.ADDON_NAME, self.CLEAN_VERSION)
        self.DEFAULT_FANART = self.ADDON.getAddonInfo("fanart")
        self.DEFAULT_ICON = self.ADDON.getAddonInfo("icon")
        self._init_kodi()
        self._init_paths()
        self.init_request(argv)
        self._init_cache()

    def _init_kodi(self):
        self.PLAYLIST = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        self.HOME_WINDOW = xbmcgui.Window(10000)
        self.KODI_FULL_VERSION = xbmc.getInfoLabel("System.BuildVersion")
        version = re.findall(r'(?:(?:((?:\d+\.?){1,3}\S+))?\s+\(((?:\d+\.?){2,3})\))', self.KODI_FULL_VERSION)
        if version:
            self.KODI_FULL_VERSION = version[0][1]
            if len(version[0][0]) > 1:
                pre_ver = version[0][0][:2]
                full_ver = version[0][1][:2]
                if pre_ver > full_ver:
                    self.KODI_VERSION = int(pre_ver[:2])
                else:
                    self.KODI_VERSION = int(full_ver[:2])
            else:
                self.KODI_VERSION = int(version[0][1][:2])
        else:
            self.KODI_FULL_VERSION = self.KODI_FULL_VERSION.split(' ')[0]
            self.KODI_VERSION = int(self.KODI_FULL_VERSION[:2])

    @staticmethod
    def _get_system_platform():
        """
        get platform on which xbmc run
        """
        platform = "unknown"
        if xbmc.getCondVisibility("system.platform.linux"):
            platform = "linux"
        elif xbmc.getCondVisibility("system.platform.xbox"):
            platform = "xbox"
        elif xbmc.getCondVisibility("system.platform.windows"):
            if "Users\\UserMgr" in os.environ.get("TMP"):
                platform = "xbox"
            else:
                platform = "windows"
        elif xbmc.getCondVisibility("system.platform.osx"):
            platform = "osx"

        return platform

    def _init_cache(self):
        try:
            import StorageServer
        except:
            import storageserverdummy as StorageServer
        
        self.CACHE = StorageServer.StorageServer("%s.animeinfo" % self.ADDON_ID, 24)

    def init_request(self, argv):
        if argv is None:
            return

        self.URL = control.urlparse(argv[0])
        try:
            self.PLUGIN_HANDLE = int(argv[1])
            self.IS_SERVICE = False
        except IndexError:
            self.PLUGIN_HANDLE = 0
            self.IS_SERVICE = True

        if self.URL[1] != "":
            self.BASE_URL = "{scheme}://{netloc}".format(
                scheme=self.URL[0], netloc=self.URL[1]
            )
        else:
            self.BASE_URL = ""
        self.PATH = control.unquote(self.URL[2])
        try:
            self.PARAM_STRING = argv[2].lstrip('?/')
        except IndexError:
            self.PARAM_STRING = ""
        self.REQUEST_PARAMS = dict(control.parse_qsl(self.PARAM_STRING))

    def _init_paths(self):
        self.ADDONS_PATH = control.translate_path(
            os.path.join("special://home/", "addons/")
        )
        self.ADDON_PATH = control.translate_path(
            os.path.join(
                "special://home/", "addons/{}".format(self.ADDON_ID.lower())
            )
        )
        self.ADDON_DATA_PATH = control.translate_path(
            self.ADDON.getAddonInfo("path")
        )  # Addon folder
        self.ADDON_USERDATA_PATH = control.translate_path(
            "special://profile/addon_data/{}/".format(self.ADDON_ID)
        )  # Addon user data folder
        self.SETTINGS_PATH = control.translate_path(
            os.path.join(self.ADDON_USERDATA_PATH, "settings.xml")
        )
        self.ADVANCED_SETTINGS_PATH = control.translate_path(
            "special://profile/advancedsettings.xml"
        )
        self.KODI_DATABASE_PATH = control.translate_path(
            "special://database/"
        )
        self.IMAGES_PATH = control.translate_path(
            os.path.join(self.ADDON_DATA_PATH, "resources", "images")
        )
        self.CACHE_DB_PATH = control.translate_path(
            os.path.join(self.ADDON_USERDATA_PATH, "cache.db")
        )
        self.TORRENT_SCRAPE_CACHE = control.translate_path(
            os.path.join(self.ADDON_USERDATA_PATH, "torrentScrape.db")
        )
        self.ANILIST_SYNC_DB_PATH = control.translate_path(
            os.path.join(self.ADDON_USERDATA_PATH, "anilistSync.db")
        )
        self.SEARCH_HISTORY_DB_PATH = control.translate_path(
            os.path.join(self.ADDON_USERDATA_PATH, "search.db")
        )
        self.MAL_DUB_FILE_PATH = control.translate_path(
            os.path.join(self.ADDON_USERDATA_PATH, "mal_dub.json")
        )

    def set_setting(self, setting_id, value):
        return self.ADDON.setSetting(setting_id, value)

    def get_setting(self, setting_id):
        return self.ADDON.getSetting(setting_id)

    def lang(self, language_id):
        text = self.ADDON.getLocalizedString(language_id)
        return control.decode_py2(text)

    def color_string(self, text, color=None):
        """Method that wraps the the text with the supplied color, or takes the user default.
        :param text:Text that needs to be wrapped
        :type text:str|int|float
        :param color:Color name used in the Kodi color tag
        :type color:str
        :return:Text wrapped in a Kodi color tag.
        :rtype:str
        """
        if color is 'default' or color is '' or color is None:
            color = 'deepskyblue'

        return "[COLOR {}]{}[/COLOR]".format(color, text)

    def close_all_dialogs(self):
        xbmc.executebuiltin("Dialog.Close(all,true)")

    def close_ok_dialog(self):
        xbmc.executebuiltin("Dialog.Close(okdialog, true)")

    def close_busy_dialog(self):
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        xbmc.executebuiltin("Dialog.Close(busydialognocancel)")

    def real_debrid_enabled(self):
        if self.get_setting('rd.auth') != '' and self.get_setting('realdebrid.enabled') == 'true':
            return True
        else:
            return False

    def all_debrid_enabled(self):
        if self.get_setting('alldebrid.apikey') != '' and self.get_setting('alldebrid.enabled') == 'true':
            return True
        else:
            return False

    def premiumize_enabled(self):
        if self.get_setting('premiumize.token') != '' and self.get_setting('premiumize.enabled') == 'true':
            return True
        else:
            return False

    def myanimelist_enabled(self):
        if self.get_setting('mal.token') != '' and self.get_setting('mal.enabled') == 'true':
            return True
        else:
            return False

    def kitsu_enabled(self):
        if self.get_setting('kitsu.token') != '' and self.get_setting('kitsu.enabled') == 'true':
            return True
        else:
            return False

    def anilist_enabled(self):
        if self.get_setting('anilist.token') != '' and self.get_setting('anilist.enabled') == 'true':
            return True
        else:
            return False

    def watchlist_to_update(self):
        if self.get_setting('watchlist.update.enabled') == 'true':
            flavor = self.get_setting('watchlist.update.flavor').lower()
            if self.get_setting('%s.enabled' % flavor) == 'true':
                return flavor
        else:
            return

    def container_refresh(self):
        return xbmc.executebuiltin("Container.Refresh")

    def allocate_item(self, name, url, is_dir=False, image='', info='', fanart=None, poster=None, is_playable=False):
        new_res = {}
        new_res['is_dir'] = is_dir
        new_res['is_playable'] = is_playable
        new_res['image'] = {
            'poster': poster,
            'thumb': image,
            'fanart': fanart
            }
        new_res['name'] = name
        new_res['url'] = url
        new_res['info'] = info
        return new_res

    def _get_view_type(self, viewType):
        viewTypes = {
            'Default': 50,
            'Poster': 51,
            'Icon Wall': 52,
            'Shift': 53,
            'Info Wall': 54,
            'Wide List': 55,
            'Wall': 500,
            'Banner': 501,
            'Fanart': 502,
        }
        return viewTypes[viewType]

    def xbmc_add_player_item(self, name, url, art='', info='', draw_cm=None, bulk_add=False):
        ok=True
        u=self.addon_url(url)
        cm = draw_cm if draw_cm is not None else []

        liz=xbmcgui.ListItem(name)
        liz.setInfo('video', info)

        if art is None or type(art) is not dict:
            art = {}

        if art.get('fanart') is None:
            art['fanart'] = self.DEFAULT_FANART
        
        liz.setArt(art)

        liz.setProperty("Video", "true")
        liz.setProperty("IsPlayable", "true")
        liz.addContextMenuItems(cm)
        if bulk_add:
            return (u, liz, False)
        else:
            ok=xbmcplugin.addDirectoryItem(handle=self.PLUGIN_HANDLE,url=u,listitem=liz, isFolder=False)
            return ok

    def xbmc_add_dir(self, name, **params):
        [params.update({key: value}) for key, value in params.items()]
        menu_item = params.pop("menu_item", {})

        liz=xbmcgui.ListItem(name)
        liz.setInfo('video', menu_item['info'])

        if menu_item.pop("is_playable", False):
            liz.setProperty("IsPlayable", "true")
            is_folder = menu_item.pop("is_dir", False)
        else:
            liz.setProperty("IsPlayable", "false")
            is_folder = menu_item.pop("is_dir", True)

        cm = params.pop("draw_cm", [])
        if cm is None or not isinstance(cm, (set, list)):
            cm = []
        liz.addContextMenuItems(cm)

        art = menu_item.pop("image", {})
        if art is None or type(art) is not dict:
            art = {}

        if art.get('fanart') is None:
            art['fanart'] = self.DEFAULT_FANART
        
        liz.setArt(art)

        bulk_add = params.pop("bulk_add", False)
        url = self.addon_url(menu_item['url'])
        if bulk_add:
            return url, liz, False
        else:
            xbmcplugin.addDirectoryItem(handle=self.PLUGIN_HANDLE,url=url,listitem=liz, isFolder=is_folder)

    def draw_items(self, video_data, contentType="tvshows", viewType=None, draw_cm=None, bulk_add=False):
        for vid in video_data:
            self.xbmc_add_dir(vid['name'], menu_item=vid, draw_cm=draw_cm, bulk_add=bulk_add)

        xbmcplugin.setContent(self.PLUGIN_HANDLE, contentType)
        if contentType == 'episodes': 
            xbmcplugin.addSortMethod(self.PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_EPISODE)
        xbmcplugin.endOfDirectory(self.PLUGIN_HANDLE, succeeded=True, updateListing=False, cacheToDisc=True)

        if viewType:
            xbmc.executebuiltin('Container.SetViewMode(%d)' % self._get_view_type(viewType))

        return True

    def bulk_draw_items(self, video_data, draw_cm=None, bulk_add=True):
        item_list = []
        for vid in video_data:
            item = self.xbmc_add_dir(vid['name'], menu_item=vid, draw_cm=draw_cm, bulk_add=bulk_add)
            item_list.append(item)

        return item_list

    def addon_url(self, url=''):
        return "{}/{}".format(self.BASE_URL, url)

    @staticmethod
    def reload_profile():
        xbmc.executebuiltin('LoadProfile({})'.format(xbmc.getInfoLabel("system.profilename")))

g = GlobalVariables()