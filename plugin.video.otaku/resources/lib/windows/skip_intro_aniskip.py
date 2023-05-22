# -*- coding: utf-8 -*-

from kodi_six import xbmc
from resources.lib.ui import control
from resources.lib.windows.base_window import BaseWindow


def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper


class SkipIntro(BaseWindow):

    def __init__(self, xml_file, xml_location, actionArgs=None):
        try:
            super(SkipIntro, self).__init__(xml_file, xml_location, actionArgs=actionArgs)
            self.player = control.player()
            self.playing_file = self.player.getPlayingFile()
            self.duration = self.player.getTotalTime() - self.player.getTime()
            # Convert duration setting to seconds
            self.skipintro_aniskip_enable = control.getSetting('skipintro.aniskip.enable') == 'false'
            self.smartplay_skipintrodialog = control.getSetting('smartplay.skipintrodialog') == 'true'

            self.closed = False
            self.actioned = None
            self.default_action = '0'

            self.current_time = None
            self.total_time = self.player.getTotalTime()

            self.skipintro_start_skip_time = None
            self.skipintro_end_skip_time = None

        except:
            # import traceback
            # traceback.print_exc()
            pass

    def onInit(self):
        self.background_tasks()

    def calculate_percent(self):
        return ((int(self.player.getTotalTime()) - int(self.player.getTime())) / float(self.duration)) * 100

    def background_tasks(self):
        self.skipintro_start_skip_time = int(control.getSetting('skipintro.start.skip.time'))
        self.skipintro_end_skip_time = int(control.getSetting('skipintro.end.skip.time'))

        try:
            # try:
            #     progress_bar = self.getControl(3014)
            # except:
            #     progress_bar = None
            self.current_time = int(self.player.getTime())
            while int(self.total_time) - int(self.current_time) > 2 and not self.closed and self.playing_file == self.player.getPlayingFile():
                self.current_time = int(self.player.getTime())

                if self.current_time > self.skipintro_end_skip_time:
                    self.close()

                elif self.current_time > 0 and self.skipintro_end_skip_time == 9999:
                    self.close()

                xbmc.sleep(500)
                # if progress_bar is not None:
                #     progress_bar.setPercent(self.calculate_percent())

            if self.default_action == '1' and\
                    self.playing_file == self.player.getPlayingFile() and\
                    not self.actioned:
                self.player.pause()
        except:
            import traceback
            traceback.print_exc()

    def doModal(self):
        try:
            super(SkipIntro, self).doModal()
        except:
            import traceback
            traceback.print_exc()

    def close(self):
        self.closed = True
        super(SkipIntro, self).close()

    def onClick(self, control_id):
        self.handle_action(7, control_id)

    @run_once
    def handle_action(self, action, control_id=None):
        if control_id is None:
            control_id = self.getFocusId()

        if control_id == 3001:
            self.actioned = True
            self.player.seekTime(self.skipintro_end_skip_time)
            self.close()
        if control_id == 3002:
            self.actioned = True
            self.close()

    def onAction(self, action):

        actionID = action.getId()

        if actionID in [92, 10, 100, 401]:
            # BACKSPACE / ESCAPE
            self.close()

        if actionID == 7:
            self.handle_action(actionID)
            return
