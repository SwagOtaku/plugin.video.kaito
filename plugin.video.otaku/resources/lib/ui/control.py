import os
import sys
import threading

import xbmcgui
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcvfs
from six.moves import urllib_parse

try:
    HANDLE = int(sys.argv[1])
except:
    HANDLE = '1'

addonInfo = xbmcaddon.Addon().getAddonInfo
ADDON_VERSION = addonInfo('version')
ADDON_NAME = addonInfo('name')
ADDON_ID = addonInfo('id')
ADDON_ICON = addonInfo('icon')
__settings__ = xbmcaddon.Addon(ADDON_ID)
__language__ = __settings__.getLocalizedString
addonInfo = __settings__.getAddonInfo
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
TRANSLATEPATH = xbmc.translatePath if PY2 else xbmcvfs.translatePath
LOGINFO = xbmc.LOGNOTICE if PY2 else xbmc.LOGINFO
INPUT_ALPHANUM = xbmcgui.INPUT_ALPHANUM
dataPath = TRANSLATEPATH(addonInfo('profile'))
ADDON_PATH = __settings__.getAddonInfo('path')
_kodiver = float(xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')[:4])

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
fanart_ = "%s/fanart.jpg" % ADDON_PATH
IMAGES_PATH = os.path.join(ADDON_PATH, 'resources', 'images')
OTAKU_LOGO_PATH = os.path.join(IMAGES_PATH, 'trans-goku.png')
OTAKU_LOGO2_PATH = os.path.join(IMAGES_PATH, 'trans-goku-small.png')
OTAKU_FANART_PATH = "%s/fanart.jpg" % ADDON_PATH
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


def log(msg, level="debug"):
    if level == "info":
        level = LOGINFO
    else:
        level = xbmc.LOGDEBUG
    xbmc.log('@@@@Otaku log:\n{0}'.format(msg), level)


def try_release_lock(lock):
    if lock.locked():
        lock.release()


def real_debrid_enabled():
    if getSetting('rd.auth') != '' and getSetting('realdebrid.enabled') == 'true':
        return True
    else:
        return False


def debrid_link_enabled():
    if getSetting('dl.auth') != '' and getSetting('dl.enabled') == 'true':
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
    return


def watchlist_enabled():
    if getSetting('watchlist.update.enabled') == 'true':
        flavor = getSetting('watchlist.update.flavor').lower()
        if getSetting('%s.enabled' % flavor) == 'true':
            return True
    return False


def copy2clip(txt):
    import subprocess
    platform = sys.platform

    if platform == 'win32':
        try:
            cmd = 'echo %s|clip' % txt.strip()
            return subprocess.check_call(cmd, shell=True)
        except:
            pass
    elif platform == 'linux2':
        try:
            from subprocess import PIPE, Popen

            p = Popen(['xsel', '-pi'], stdin=PIPE)
            p.communicate(input=txt)
        except:
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


def lang(x):
    return __language__(x)


def addon_url(url=''):
    return "plugin://%s/%s" % (ADDON_ID, url)


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


def textviewer_dialog(title, text):
    return xbmcgui.Dialog().textviewer(title, text)


def yesno_dialog(title, text, nolabel=None, yeslabel=None):
    return xbmcgui.Dialog().yesno(title, text, nolabel=nolabel, yeslabel=yeslabel)


def notify(text):
    xbmcgui.Dialog().notification(ADDON_NAME, text, ADDON_ICON, 5000, False)


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

    import os
    import shutil

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


def make_listitem(name, labels):
    li = xbmcgui.ListItem(name)
    cast2 = labels.pop('cast2') if isinstance(labels, dict) and 'cast2' in labels.keys() else []
    if _kodiver > 19.8 and isinstance(labels, dict):
        vtag = li.getVideoInfoTag()
        if labels.get('mediatype'):
            vtag.setMediaType(labels['mediatype'])
        if labels.get('title'):
            vtag.setTitle(labels['title'])
        if labels.get('tvshowtitle'):
            vtag.setTvShowTitle(labels['tvshowtitle'])
        if labels.get('plot'):
            vtag.setPlot(labels['plot'])
        if labels.get('year'):
            vtag.setYear(int(labels['year']))
        if labels.get('premiered'):
            vtag.setPremiered(labels['premiered'])
        if labels.get('status'):
            vtag.setTvShowStatus(labels['status'])
        if labels.get('duration'):
            vtag.setDuration(labels['duration'])
        if labels.get('country'):
            vtag.setCountries([labels['country']])
        if labels.get('genre'):
            vtag.setGenres(labels['genre'])
        if labels.get('studio'):
            vtag.setStudios(labels['studio'])
        if labels.get('rating'):
            vtag.setRating(labels['rating'])
        if labels.get('trailer'):
            vtag.setTrailer(labels['trailer'])
        if labels.get('season'):
            vtag.setSeason(int(labels['season']))
        if labels.get('episode'):
            vtag.setEpisode(int(labels['episode']))
        if labels.get('aired'):
            vtag.setFirstAired(labels['aired'])
        if labels.get('playcount'):
            vtag.setPlaycount(labels['playcount'])

        if cast2:
            cast2 = [xbmc.Actor(p['name'], p['role'], cast2.index(p), p['thumbnail']) for p in cast2]
            vtag.setCast(cast2)

    else:
        li.setInfo(type='Video', infoLabels=labels)
        if cast2:
            li.setCast(cast2)
    return li


def xbmc_add_player_item(name, url, art={}, info={}, draw_cm=None, bulk_add=False):
    u = addon_url(url)
    cm = []
    if draw_cm is not None:
        if isinstance(draw_cm, list):
            for draw in draw_cm:
                cm.append((draw[0], 'RunPlugin(plugin://{0}/{1}/{2})'.format(ADDON_ID, draw[1], url)))

    liz = make_listitem(name, info)

    if art is None or type(art) is not dict:
        art = {}

    if art.get('fanart') is None:
        art['fanart'] = OTAKU_FANART_PATH

    liz.setArt(art)
    liz.setProperty("Video", "true")
    liz.setProperty("IsPlayable", "true")
    liz.addContextMenuItems(cm)
    if bulk_add:
        return u, liz, False
    else:
        return xbmcplugin.addDirectoryItem(handle=HANDLE, url=u, listitem=liz, isFolder=False)


def xbmc_add_dir(name, url, art={}, info={}, draw_cm=None):
    u = addon_url(url)
    # cm = [('Trakt Meta Correction', 'RunPlugin(plugin://{0}/trakt_correction/{1})'.format(ADDON_ID, url))]
    cm = []
    if draw_cm is not None:
        if isinstance(draw_cm, list):
            for draw in draw_cm:
                cm.append((draw[0], 'RunPlugin(plugin://{0}/{1}/{2})'.format(ADDON_ID, draw[1], url)))
    else:
        if watchlist_enabled():
            cm.append(('Add to Watchlist', 'RunPlugin(plugin://{0}/add_to_watchlist/{1})'.format(ADDON_ID, url)))
            cm.append(('Mark as Completed', 'RunPlugin(plugin://{0}/add_to_completed_watchlist/{1})'.format(ADDON_ID, url)))

    liz = make_listitem(name, info)

    if art is None or type(art) is not dict:
        art = {}

    if art.get('fanart') is None:
        art['fanart'] = OTAKU_FANART_PATH

    liz.setArt(art)
    liz.addContextMenuItems(cm)

    return xbmcplugin.addDirectoryItem(handle=HANDLE, url=u, listitem=liz, isFolder=True)


def draw_items(video_data, contentType="tvshows", viewType=None, draw_cm=None, bulk_add=False):
    if isinstance(video_data, tuple):
        contentType = video_data[1]
        video_data = video_data[0]

    if not isinstance(video_data, list):
        video_data = [video_data]

    for vid in video_data:
        if vid['is_dir']:
            xbmc_add_dir(vid['name'], vid['url'], vid['image'], vid['info'], draw_cm)
        else:
            if draw_cm is None:
                if contentType != 'episodes' and watchlist_enabled():
                    draw_cm = [('Add to Watchlist', 'add_to_watchlist'), ('Mark as Completed', 'add_to_completed_watchlist')]
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


def artPath():
    THEMES = ['coloured', 'white']
    if condVisibility('System.HasAddon(script.otaku.themepak)'):
        return os.path.join(
            xbmcaddon.Addon('script.otaku.themepak').getAddonInfo('path'),
            'art',
            'themes',
            THEMES[int(getSetting("general.icons"))]
        )


def getKodiVersion():
    return int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0])


def getChangeLog():
    addon_version = xbmcaddon.Addon('plugin.video.otaku').getAddonInfo('version')
    changelog_file = os.path.join(ADDON_PATH, 'changelog.txt')
    news_file = os.path.join(ADDON_PATH, 'news.txt')

    # Read changelog file
    changelog_text = ""
    if xbmcvfs.exists(changelog_file):
        if PY2:
            f = open(changelog_file, 'r')
        else:
            f = open(changelog_file, 'r', encoding='utf-8', errors='ignore')
        changelog_text = f.read()
        f.close()
    else:
        return xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % ('Otaku', 'Changelog file not found.', 5000, xbmcgui.NOTIFICATION_ERROR))

    # Read news file
    news_text = ""
    if xbmcvfs.exists(news_file):
        if PY2:
            f = open(news_file, 'r')
        else:
            f = open(news_file, 'r', encoding='utf-8', errors='ignore')
        news_text = f.read()
        f.close()

    # Combine changelog and news text
    text = changelog_text
    text_2 = news_text
    heading = '[B]%s -  v%s - ChangeLog & News[/B]' % ('Otaku', addon_version)
    from resources.lib.windows.textviewer import TextViewerXML
    windows = TextViewerXML('textviewer.xml', ADDON_PATH, heading=heading, text=text, text_2=text_2)
    windows.run()
    del windows


def getInstructions():
    addon_version = xbmcaddon.Addon('plugin.video.otaku').getAddonInfo('version')
    instructions_file = os.path.join(ADDON_PATH, 'instructions.txt')
    if not xbmcvfs.exists(instructions_file):
        return xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % ('Otaku', 'Instructions file not found.', 5000, xbmcgui.NOTIFICATION_ERROR))
    if PY2:
        f = open(instructions_file, 'r')
    else:
        f = open(instructions_file, 'r', encoding='utf-8', errors='ignore')
    text = f.read()
    f.close()
    heading = '[B]%s -  v%s - Instructions[/B]' % ('Otaku', addon_version)
    from resources.lib.windows.textviewer import TextViewerXML
    windows = TextViewerXML('textviewer_1.xml', ADDON_PATH, heading=heading, text=text)
    # windows = TextViewerXML(*('textviewer_1.xml', ADDON_PATH),heading=heading, text=text).doModal()
    windows.run()
    del windows

def setGlobalProp(property, value):
    xbmcgui.Window(10000).setProperty(property, str(value))
def getGlobalProp(property):
    value = xbmcgui.Window(10000).getProperty(property)
    if value.lower in ("true", "false"):
        return value.lower == "true"
    else:
        return value