# -*- coding: utf-8 -*-
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import re
import os
import threading
import sys
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
from . import http
import urllib.parse
from urllib.parse import quote

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

try:
    HANDLE=int(sys.argv[1])
except:
    HANDLE = '1'

PYTHON3 = True if sys.version_info.major == 3 else False

addonInfo = xbmcaddon.Addon().getAddonInfo
ADDON_NAME = addonInfo('id')
__settings__ = xbmcaddon.Addon(ADDON_NAME)
__language__ = __settings__.getLocalizedString
CACHE = StorageServer.StorageServer("%s.animeinfo" % ADDON_NAME, 24)
addonInfo = __settings__.getAddonInfo
try:
    dataPath = xbmc.translatePath(addonInfo('profile')).decode('utf-8')
except:
    dataPath = xbmc.translatePath(addonInfo('profile'))

try:
    ADDON_PATH = __settings__.getAddonInfo('path').decode('utf-8')
except:
    ADDON_PATH = __settings__.getAddonInfo('path')


cacheFile = os.path.join(dataPath, 'cache.db')
cacheFile_lock = threading.Lock()

searchHistoryDB = os.path.join(dataPath, 'search.db')
searchHistoryDB_lock = threading.Lock()
anilistSyncDB = os.path.join(dataPath, 'anilistSync.db')
anilistSyncDB_lock = threading.Lock()
torrentScrapeCacheFile = os.path.join(dataPath, 'torrentScrape.db')
torrentScrapeCacheFile_lock = threading.Lock()

maldubFile = os.path.join(dataPath, 'mal_dub.json')

kodiGui = xbmcgui
showDialog = xbmcgui.Dialog()
dialogWindow = kodiGui.WindowDialog
xmlWindow = kodiGui.WindowXMLDialog
condVisibility = xbmc.getCondVisibility
fanart_ = ADDON_PATH + "/fanart.jpg"
IMAGES_PATH = os.path.join(ADDON_PATH, 'resources', 'images')
KAITO_LOGO_PATH = os.path.join(IMAGES_PATH, 'trans-crow.png')
KAITO_FANART_PATH = ADDON_PATH + "/fanart.jpg"
menuItem = xbmcgui.ListItem
execute = xbmc.executebuiltin

progressDialog = xbmcgui.DialogProgress()
kodi = xbmc

playList = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
player = xbmc.Player

try:
    basestring = basestring  # noqa # pylint: disable=undefined-variable
    unicode = unicode  # noqa # pylint: disable=undefined-variable
    xrange = xrange  # noqa # pylint: disable=undefined-variable
except NameError:
    basestring = str
    unicode = str
    xrange = range

def decode_py2(value):
    if not PYTHON3 and isinstance(value, basestring):
        return encode_py2(value).decode("utf-8")
    return value

def encode_py2(value):
    if not value:
        return value
    if not PYTHON3 and isinstance(value, unicode):
        return value.encode("utf-8")
    return value

def closeBusyDialog():
    if condVisibility('Window.IsActive(busydialog)'):
        execute('Dialog.Close(busydialog)')
    if condVisibility('Window.IsActive(busydialognocancel)'):
        execute('Dialog.Close(busydialognocancel)')

def try_release_lock(lock):
    if lock.locked():
        lock.release()

def real_debrid_enabled():
    if getSetting('rd.auth') != '' and getSetting('realdebrid.enabled') == 'true':
        return True
    else:
        return False

def all_debrid_enabled():
    if getSetting('alldebrid.apikey') != '' and getSetting('alldebrid.enabled') == 'true':
        return True
    else:
        return False

def premiumize_enabled():
    if getSetting('premiumize.token') != '' and getSetting('premiumize.enabled') == 'true':
        return True
    else:
        return False

def myanimelist_enabled():
    if getSetting('mal.token') != '' and getSetting('mal.enabled') == 'true':
        return True
    else:
        return False

def kitsu_enabled():
    if getSetting('kitsu.token') != '' and getSetting('kitsu.enabled') == 'true':
        return True
    else:
        return False

def anilist_enabled():
    if getSetting('anilist.token') != '' and getSetting('anilist.enabled') == 'true':
        return True
    else:
        return False

def watchlist_to_update():
    if getSetting('watchlist.update.enabled') == 'true':
        flavor = getSetting('watchlist.update.flavor').lower()
        if getSetting('%s.enabled' % flavor) == 'true':
            return flavor
    else:
        return

def copy2clip(txt):
    import subprocess
    platform = sys.platform

    if platform == 'win32':
        try:
            cmd = 'echo ' + txt.strip() + '|clip'
            return subprocess.check_call(cmd, shell=True)
            pass
        except:
            pass
    elif platform == 'linux2':
        try:
            from subprocess import Popen, PIPE

            p = Popen(['xsel', '-pi'], stdin=PIPE)
            p.communicate(input=txt)
        except:
            pass
    else:
        pass
    pass

def colorString(text, color=None):
    if color is 'default' or color is '' or color is None:
        color = 'deepskyblue'

    return '[COLOR %s]%s[/COLOR]' % (color, text)

def create_multiline_message(line1=None, line2=None, line3=None, *lines):
    """Creates a message from the supplied lines
    :param line1:Line 1
    :type line1:str
    :param line2:Line 2
    :type line2:str
    :param line3: Line3
    :type line3:str
    :param lines:List of additional lines
    :type lines:list[str]
    :return:New message wit the combined lines
    :rtype:str
    """
    result = []
    if line1:
        result.append(line1)
    if line2:
        result.append(line2)
    if line3:
        result.append(line3)
    if lines:
        result.extend(l for l in lines if l)
    return "\n".join(result)

def refresh():
    return xbmc.executebuiltin('Container.Refresh')

def settingsMenu():
    return xbmcaddon.Addon().openSettings()

def getSetting(key):
    return __settings__.getSetting(key)

def setSetting(id, value):
    return __settings__.setSetting(id=id, value=value)

def cache(funct, *args):
    return CACHE.cacheFunction(funct, *args)

def clear_cache():
    return CACHE.delete("%")

def lang(x):
    text = __language__(x)
    return decode_py2(text)

def addon_url(url=''):
    return "plugin://%s/%s" % (ADDON_NAME, url)

def get_plugin_url():
    addon_base = addon_url()
    assert sys.argv[0].startswith(addon_base), "something bad happened in here"
    return sys.argv[0][len(addon_base):]

def get_plugin_params():
    return dict(urllib.parse.parse_qsl(sys.argv[2].replace('?', '')))

def keyboard(text):
    keyboard = xbmc.Keyboard("", text, False)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    return None

def closeAllDialogs():
    execute('Dialog.Close(all,true)')

def ok_dialog(title, text):
    return xbmcgui.Dialog().ok(title, text)

def yesno_dialog(title, text, nolabel=None, yeslabel=None):
    return xbmcgui.Dialog().yesno(title, text, nolabel=nolabel, yeslabel=yeslabel)

def multiselect_dialog(title, _list):
    if isinstance(_list, list):
        return xbmcgui.Dialog().multiselect(title, _list)
    return None

def clear_settings(dialog):
    confirm = dialog
    if confirm == 0:
        return

    addonInfo = __settings__.getAddonInfo
    try:
        dataPath = xbmc.translatePath(addonInfo('profile')).decode('utf-8')
    except:
        dataPath = xbmc.translatePath(addonInfo('profile'))

    import shutil
    import os

    if os.path.exists(dataPath):
        shutil.rmtree(dataPath)

    os.mkdir(dataPath)
    refresh()

def _get_view_type(viewType):
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

def xbmc_add_player_item(name, url, art='', info='', draw_cm=None, bulk_add=False):
    ok=True
    u=addon_url(url)
    cm = draw_cm(addon_url, name) if draw_cm is not None else []

    liz=xbmcgui.ListItem(name)
    liz.setInfo('video', info)

    if art is None or type(art) is not dict:
        art = {}

    if art.get('fanart') is None:
        art['fanart'] = KAITO_FANART_PATH
    
    liz.setArt(art)

    liz.setProperty("Video", "true")
    liz.setProperty("IsPlayable", "true")
    liz.addContextMenuItems(cm)
    if bulk_add:
        return (u, liz, False)
    else:
        ok=xbmcplugin.addDirectoryItem(handle=HANDLE,url=u,listitem=liz, isFolder=False)
        return ok

def xbmc_add_dir(name, url, art='', info='', draw_cm=None):
    ok=True
    u=addon_url(url)
    cm = draw_cm(addon_url, name) if draw_cm is not None else []

    liz=xbmcgui.ListItem(name)
    liz.setInfo('video', info)

    if art is None or type(art) is not dict:
        art = {}

    if art.get('fanart') is None:
        art['fanart'] = KAITO_FANART_PATH
    
    liz.setArt(art)

    liz.addContextMenuItems(cm)
    ok=xbmcplugin.addDirectoryItem(handle=HANDLE,url=u,listitem=liz,isFolder=True)
    return ok

def draw_items(video_data, contentType="tvshows", viewType=None, draw_cm=None, bulk_add=False):
    for vid in video_data:
        if vid['is_dir']:
            xbmc_add_dir(vid['name'], vid['url'], vid['image'], vid['info'], draw_cm)
        else:
            xbmc_add_player_item(vid['name'], vid['url'], vid['image'],
                                 vid['info'], draw_cm, bulk_add)

    xbmcplugin.setContent(HANDLE, contentType)
    if contentType == 'episodes': 
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True, updateListing=False, cacheToDisc=True)

    if viewType:
        xbmc.executebuiltin('Container.SetViewMode(%d)' % _get_view_type(viewType))

    return True

def bulk_draw_items(video_data, draw_cm=None, bulk_add=True):
    item_list = []
    for vid in video_data:
        item = xbmc_add_player_item(vid['name'], vid['url'], vid['image'],
                                    vid['info'], draw_cm, bulk_add)
        item_list.append(item)

    return item_list
