# -*- coding: utf-8 -*-
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import re
import os
import threading
import sys
import xbmc
import xbmcvfs
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


kodiGui = xbmcgui
showDialog = xbmcgui.Dialog()
dialogWindow = kodiGui.WindowDialog
xmlWindow = kodiGui.WindowXMLDialog
condVisibility = xbmc.getCondVisibility
menuItem = xbmcgui.ListItem
execute = xbmc.executebuiltin

progressDialog = xbmcgui.DialogProgress()
kodi = xbmc

playList = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
player = xbmc.Player

try:
    # Try to get Python 3 versions
    from urllib.parse import (
        parse_qsl,
        urlencode,
        quote_plus,
        parse_qs,
        quote,
        unquote,
        urlparse,
        urljoin,
    )
except ImportError:
    # Fall back on future.backports to ensure we get unicode compatible PY3 versions in PY2
    from future.backports.urllib.parse import (
        parse_qsl,
        urlencode,
        quote_plus,
        parse_qs,
        quote,
        unquote,
        urlparse,
        urljoin,
    )

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

def validate_path(path):
    """Returns the translated path.
    :param path:Path to format
    :type path:str
    :return:Translated path
    :rtype:str
    """
    if hasattr(xbmcvfs, "validatePath"):
        path = xbmcvfs.validatePath(path)  # pylint: disable=no-member
    else:
        path = xbmc.validatePath(path)  # pylint: disable=no-member
    return path

def translate_path(path):
    """Validates the path against the running platform and ouputs the clean path.
    :param path:Path to be verified
    :type path:str
    :return:Verified and cleaned path
    :rtype:str
    """
    if hasattr(xbmcvfs, "translatePath"):
        path = xbmcvfs.translatePath(path)  # pylint: disable=no-member
    else:
        path = xbmc.translatePath(path)  # pylint: disable=no-member
    return path

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