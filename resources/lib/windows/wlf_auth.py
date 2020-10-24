# -*- coding: utf-8 -*-

import time
from resources.lib.ui import control
from resources.lib.windows.base_window import BaseWindow
from resources.lib.windows.resolver import Resolver
from resources.lib.ui import database

class WatchlistFlavorAuth(BaseWindow):

    def __init__(self, xml_file, location, flavor=None, sources=None, **kwargs):
        super(WatchlistFlavorAuth, self).__init__(xml_file, location)
        self.flavor = flavor
        self.sources = sources
        self.position = -1
        self.last_action = 0
        control.closeBusyDialog()
        self.authorized = False

    def onInit(self):
        self.setFocusId(1000)

    def doModal(self):
        super(WatchlistFlavorAuth, self).doModal()
        return self.authorized

    def onClick(self, controlId):

        if controlId == 1000:
            self.handle_action(7)

    def handle_action(self, actionID):
        if (time.time() - self.last_action) < .5:
            return

        if actionID == 7 and self.getFocusId() == 1002:
            self.set_settings()

        if actionID == 7 and self.getFocusId() == 1003:
            self.close()

        if actionID == 92 or id == 10:
            self.close()

        self.last_action = time.time()

    def onAction(self, action):
        actionID = action.getId()

        if actionID in [7, 92, 10]:
            self.handle_action(actionID)

    def set_settings(self):
        res = {}
        if self.flavor == 'anilist':
            res['username'] = self.getControl(1000).getText()
            res['token'] = self.getControl(1001).getText()
        else:
            res['authvar'] = self.getControl(1000).getText()

        for _id, value in res.items():
            control.setSetting('%s.%s' % (self.flavor, _id), value)

        self.authorized = True
        self.close()

class AltWatchlistFlavorAuth:
    def __init__(self, flavor=None):
        self.flavor = flavor
        self.authorized = False

    def set_settings(self):
        res = {}
        dialog = control.kodiGui.Dialog()
        if self.flavor == 'anilist':
            res['username'] = dialog.input('Enter AniList username', type=control.kodiGui.INPUT_ALPHANUM)
            res['token'] = dialog.input('Enter AniList token', type=control.kodiGui.INPUT_ALPHANUM)
        else:
            res['authvar'] = dialog.input('Enter MAL auth url', type=control.kodiGui.INPUT_ALPHANUM)

        try:
            for _id, value in res.items():
                if not value:
                    raise Exception

                control.setSetting('%s.%s' % (self.flavor, _id), value)
                self.authorized = True
        except:
            pass

        return self.authorized
