# -*- coding: utf-8 -*-
import xbmcgui
import time
from . import control

def refresh_apis():
    rd_token = control.getSetting('rd.auth')
    rd_expiry = int(float(control.getSetting('rd.expiry')))
    kitsu_token = control.getSetting('kitsu.token')
    mal_token = control.getSetting('mal.token')

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
            kitsu_expiry = int(float(control.getSetting('kitsu.expiry')))
            if time.time() > (kitsu_expiry - (10 * 60)):
                from resources.lib.WatchlistFlavor import Kitsu
                Kitsu.KitsuWLF().refresh_token(control)
    except:
        pass

    try:
        if mal_token != '':
            mal_expiry = int(float(control.getSetting('mal.expiry')))
            if time.time() > (mal_expiry - (10 * 60)):
                from resources.lib.WatchlistFlavor import MyAnimeList
                MyAnimeList.MyAnimeListWLF().refresh_token(control)
    except:
        pass

def run_maintenance():

##    tools.log('Performing Maintenance')
    # ADD COMMON HOUSE KEEPING ITEMS HERE #

    # Refresh API tokens
    try:
        refresh_apis()
    except:
        pass
