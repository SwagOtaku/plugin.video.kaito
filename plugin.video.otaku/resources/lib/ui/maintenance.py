# -*- coding: utf-8 -*-
import xbmcgui
import xbmcvfs
import time
import os
from resources.lib.ui import control
from resources.lib.ui.globals import g

def refresh_apis():
    rd_token = g.get_setting('rd.auth')
    rd_expiry = int(float(g.get_setting('rd.expiry')))
    kitsu_token = g.get_setting('kitsu.token')
    mal_token = g.get_setting('mal.token')

    try:
        if rd_token != '':
            if time.time() > (rd_expiry - (10 * 60)):
                from resources.lib.debrid import real_debrid
##                tools.log('Service Refreshing Real Debrid Token')
                real_debrid.Debrid().refreshToken()
    except:
        pass

    try:
        if kitsu_token != '':
            kitsu_expiry = int(float(g.get_setting('kitsu.expiry')))
            if time.time() > (kitsu_expiry - (10 * 60)):
                from resources.lib.WatchlistFlavor import Kitsu
                Kitsu.KitsuWLF().refresh_token()
    except:
        pass

    try:
        if mal_token != '':
            mal_expiry = int(float(g.get_setting('mal.expiry')))
            if time.time() > (mal_expiry - (10 * 60)):
                from resources.lib.WatchlistFlavor import MyAnimeList
                MyAnimeList.MyAnimeListWLF().refresh_token()
    except:
        pass

def wipe_install():
    """
    Destroys kaito's user_data folder for current user resetting addon to default
    :return: None
    :rtype: None
    """
    confirm = xbmcgui.Dialog().yesno(g.ADDON_NAME, g.lang(30025))
    if confirm == 0:
        return

    # confirm = xbmcgui.Dialog().yesno(
    #     g.ADDON_NAME,
    #     g.lang(30035)
    #     + "{}".format(g.color_string(g.lang(30036))),
    # )
    # if confirm == 0:
    #     return

    path = control.validate_path(g.ADDON_USERDATA_PATH)
    if xbmcvfs.exists(path):
        xbmcvfs.rmdir(path, True)
    xbmcvfs.mkdir(g.ADDON_USERDATA_PATH)

def toggle_reuselanguageinvoker(forced_state=None):

    def _store_and_reload(output):
        with open(file_path, "w+") as addon_xml:
            addon_xml.writelines(output)
        xbmcgui.Dialog().ok(g.ADDON_NAME, 'Language Invoker option has been changed, reloading kodi profile')
        g.reload_profile()

    file_path = os.path.join(g.ADDON_DATA_PATH, "addon.xml")

    with open(file_path, "r") as addon_xml:
        file_lines = addon_xml.readlines()

    for i in range(len(file_lines)):
        line_string = file_lines[i]
        if "reuselanguageinvoker" in file_lines[i]:
            if ("false" in line_string and forced_state is None) or ("false" in line_string and forced_state):
                file_lines[i] = file_lines[i].replace("false", "true")
                g.set_setting("reuselanguageinvoker.status", "Enabled")
                _store_and_reload(file_lines)
            elif ("true" in line_string and forced_state is None) or ("true" in line_string and forced_state is False):
                file_lines[i] = file_lines[i].replace("true", "false")
                g.set_setting("reuselanguageinvoker.status", "Disabled")
                _store_and_reload(file_lines)
            break

def run_maintenance():

##    tools.log('Performing Maintenance')
    # ADD COMMON HOUSE KEEPING ITEMS HERE #

    # Refresh API tokens
    try:
        refresh_apis()
    except:
        pass