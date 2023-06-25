from resources.lib.ui import database, control
from kodi_six import xbmc, xbmcgui

class  SettingsMonitor(xbmc.Monitor):
    def __init__(self):
        while (not self.abortRequested()):
            xbmc.sleep(1000)
    def onSettingsChanged(self):
        control.calendarRefresh = True