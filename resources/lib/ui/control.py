import os
import threading
import sys
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcvfs
import xbmcgui
from six.moves import urllib_parse

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

try:
    HANDLE = int(sys.argv[1])
except:
    HANDLE = '1'

addonInfo = xbmcaddon.Addon().getAddonInfo
ADDON_NAME = addonInfo('id')
__settings__ = xbmcaddon.Addon(ADDON_NAME)
__language__ = __settings__.getLocalizedString
CACHE = StorageServer.StorageServer("%s.animeinfo" % ADDON_NAME, 24)
addonInfo = __settings__.getAddonInfo
PY2 = sys.version_info[0] == 2
TRANSLATEPATH = xbmc.translatePath if PY2 else xbmcvfs.translatePath
LOGINFO = xbmc.LOGNOTICE if PY2 else xbmc.LOGINFO
INPUT_ALPHANUM = xbmcgui.INPUT_ALPHANUM
dataPath = TRANSLATEPATH(addonInfo('profile'))
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

showDialog = xbmcgui.Dialog()
dialogWindow = xbmcgui.WindowDialog
xmlWindow = xbmcgui.WindowXMLDialog
condVisibility = xbmc.getCondVisibility
sleep = xbmc.sleep
fanart_ = ADDON_PATH + "/fanart.jpg"
IMAGES_PATH = os.path.join(ADDON_PATH, 'resources', 'images')
KAITO_LOGO_PATH = os.path.join(IMAGES_PATH, 'trans-crow.png')
KAITO_FANART_PATH = ADDON_PATH + "/fanart.jpg"
menuItem = xbmcgui.ListItem
execute = xbmc.executebuiltin

progressDialog = xbmcgui.DialogProgress()

playList = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
player = xbmc.Player


def closeBusyDialog():
    if condVisibility('Window.IsActive(busydialog)'):
        execute('Dialog.Close(busydialog)')
    if condVisibility('Window.IsActive(busydialognocancel)'):
        execute('Dialog.Close(busydialognocancel)')


def log(msg, level=xbmc.LOGDEBUG):
    xbmc.log('@@@@Kaito log:\n{0}'.format(msg), level)


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
    if color == 'default' or color == '' or color is None:
        color = 'deepskyblue'

    return '[COLOR %s]%s[/COLOR]' % (color, text)


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
    return __language__(x)


def addon_url(url=''):
    return "plugin://%s/%s" % (ADDON_NAME, url)


def get_plugin_url():
    addon_base = addon_url()
    assert sys.argv[0].startswith(addon_base), "something bad happened in here"
    return sys.argv[0][len(addon_base):]


def get_plugin_params():
    return dict(urllib_parse.parse_qsl(sys.argv[2].replace('?', '')))


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
    dataPath = TRANSLATEPATH(addonInfo('profile'))

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
    ok = True
    u = addon_url(url)
    cm = draw_cm(addon_url, name) if draw_cm is not None else []

    liz = xbmcgui.ListItem(name)
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
        ok = xbmcplugin.addDirectoryItem(handle=HANDLE, url=u, listitem=liz, isFolder=False)
        return ok


def xbmc_add_dir(name, url, art='', info='', draw_cm=None):
    ok = True
    u = addon_url(url)
    cm = draw_cm(addon_url, name) if draw_cm is not None else []

    liz = xbmcgui.ListItem(name)
    liz.setInfo('video', info)

    if art is None or type(art) is not dict:
        art = {}

    if art.get('fanart') is None:
        art['fanart'] = KAITO_FANART_PATH

    liz.setArt(art)

    liz.addContextMenuItems(cm)
    ok = xbmcplugin.addDirectoryItem(handle=HANDLE, url=u, listitem=liz, isFolder=True)
    return ok


def draw_items(video_data, contentType="tvshows", viewType=None, draw_cm=None, bulk_add=False):
    if isinstance(video_data, tuple):
        video_data, contentType = video_data

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
