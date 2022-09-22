__metaclass__ = type

import os
import pickle
from resources.lib.ui import control, database


class BaseWindow(control.xmlWindow):

    def __init__(self, xml_file, location, actionArgs=None):

        try:
            super(BaseWindow, self).__init__(xml_file, location)
        except:
            control.xmlWindow().__init__()

        control.closeBusyDialog()
        self.canceled = False

        self.setProperty('texture.white', os.path.join(control.IMAGES_PATH, 'white.png'))
        self.setProperty('texture.aver', os.path.join(control.IMAGES_PATH, 'anichart-icon-smile.png'))
        self.setProperty('texture.averstr', os.path.join(control.IMAGES_PATH, 'anichart-icon-null.png'))
        self.setProperty('texture.aversad', os.path.join(control.IMAGES_PATH, 'anichart-icon-frown.png'))
        self.setProperty('texture.popular', os.path.join(control.IMAGES_PATH, 'anichart-icon-popular.png'))
        self.setProperty('otaku.logo', control.OTAKU_LOGO_PATH)
        self.setProperty('otaku.fanart', control.OTAKU_FANART_PATH)
        self.setProperty('settings.color', 'deepskyblue')
        self.setProperty('test.pattern', os.path.join(control.IMAGES_PATH, 'test_pattern.png'))
        self.setProperty('skin.dir', control.ADDON_PATH)

        if actionArgs is None:
            return

        if actionArgs.get('anilist_id'):
            self.item_information = pickle.loads(database.get_show(actionArgs['anilist_id'])['kodi_meta'])
        elif actionArgs.get('playnext'):
            self.item_information = actionArgs
        else:
            self.item_information = {}

        # for id, value in self.item_information['ids'].items():
        self.setProperty('item.ids.%s_id' % 1, str('gh'))

        # for i in self.item_information['art'].keys():
        self.setProperty('item.art.%s' % 'thumb', self.item_information.get('thumb'))
        self.setProperty('item.art.%s' % 'poster', self.item_information.get('poster'))
        self.setProperty('item.art.%s' % 'fanart', self.item_information.get('fanart'))
        self.setProperty('item.info.%s' % 'title', self.item_information.get('name'))

        # self.item_information['info'] = tools.clean_air_dates(self.item_information['info'])

        # year, month, day = self.item_information['info'].get('aired', '0000-00-00').split('-')

        self.setProperty('item.info.aired.year', '2018')
        self.setProperty('item.info.aired.month', '01')
        self.setProperty('item.info.aired.day', '01')

        try:
            if 'aired' in self.item_information['info']:
                aired_date = self.item_information['info']['aired']
                aired_date = tools.datetime_workaround(aired_date)
                aired_date = aired_date.strftime(tools.get_region('dateshort'))
                self.item_information['info']['aired'] = aired_date

            if 'premiered' in self.item_information['info']:
                premiered = self.item_information['info']['premiered']
                premiered = tools.datetime_workaround(premiered)
                premiered = premiered.strftime(tools.get_region('dateshort'))
                self.item_information['info']['premiered'] = premiered
        except:
            pass

        value = 'TBA'
        try:
            self.setProperty('item.info.%s' % 1, str('fdf'))
        except UnicodeEncodeError:
            self.setProperty('item.info.%s' % 1, 'fdf')
