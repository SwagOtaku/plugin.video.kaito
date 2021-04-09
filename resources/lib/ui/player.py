# -*- coding: utf-8 -*-
from __future__ import absolute_import
from builtins import range
from builtins import object
import sys
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
from . import http

from . import control

try:
    HANDLE=int(sys.argv[1])
except:
    HANDLE = '1'

addonInfo = xbmcaddon.Addon().getAddonInfo
ADDON_NAME = addonInfo('id')
__settings__ = xbmcaddon.Addon(ADDON_NAME)
addonInfo = __settings__.getAddonInfo

try:
    ADDON_PATH = __settings__.getAddonInfo('path').decode('utf-8')
except:
    ADDON_PATH = __settings__.getAddonInfo('path')

kodiGui = xbmcgui
execute = xbmc.executebuiltin

playList = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
player = xbmc.Player

progressDialog = xbmcgui.DialogProgress()
kodi = xbmc

class hook_mimetype(object):
    __MIME_HOOKS = {}

    @classmethod
    def trigger(cls, mimetype, item):

        if mimetype in list(cls.__MIME_HOOKS.keys()):
            return cls.__MIME_HOOKS[mimetype](item)

        return item

    def __init__(self, mimetype):
        self._type = mimetype

    def __call__(self, func):
        assert self._type not in list(self.__MIME_HOOKS.keys())
        self.__MIME_HOOKS[self._type] = func
        return func

class watchlistPlayer(xbmc.Player):

    def __init__(self):
        super(watchlistPlayer, self).__init__()
        self._on_playback_done = None
        self._on_stopped = None
        self._on_percent = None
        self._watchlist_update = None
        self.current_time = 0
        self.updated = False
        self.media_type = None
##        self.AVStarted = False

    def handle_player(self, anilist_id, watchlist_update, build_playlist, episode, filter_lang):
        self._anilist_id = anilist_id

        if watchlist_update:
            self._watchlist_update = watchlist_update(anilist_id, episode)

        self._build_playlist = build_playlist
        self._episode = episode
        self._filter_lang = filter_lang
        self.keepAlive()
        
    def onPlayBackStarted(self):
        if self._build_playlist and playList.size() == 1:
            self._build_playlist(self._anilist_id, self._episode, self._filter_lang)

        current_ = playList.getposition()
        self.media_type = playList[current_].getVideoInfoTag().getMediaType()
        control.setSetting('addon.last_watched', self._anilist_id)
        pass

##    def onAVStarted(self):
##        self.AVStarted = True
##
##    def onAVChange(self):
##        self.AVStarted = True

    def onPlayBackStopped(self):
        playList.clear()

##    def onPlayBackEnded(self):
##        pass

    def onPlayBackError(self):
        playList.clear()
        sys.exit(1)

    def getWatchedPercent(self):
        try:
            current_position = self.getTime()
        except:
            current_position = self.current_time

        media_length = self.getTotalTime()
        watched_percent = 0

        if int(media_length) is not 0:
            watched_percent = float(current_position) / float(media_length) * 100

        return watched_percent

    def onWatchedPercent(self):
        if not self._watchlist_update:
            return

        while self.isPlaying() and not self.updated:
            try:
                watched_percentage = self.getWatchedPercent()

                try:
                    self.current_time = self.getTime()

                except:
                    import traceback
                    traceback.print_exc()
                    pass

                if watched_percentage > 80:
                    self._watchlist_update()
                    self.updated = True
                    break

            except:
                import traceback
                traceback.print_exc()
                xbmc.sleep(1000)
                continue

            xbmc.sleep(1000)

        else:
            return

    def keepAlive(self):
        for i in range(0, 480):
            if self.isPlayingVideo():
                break
            xbmc.sleep(250)

##        for i in range(0, 480):
##            if self.AVStarted:
##                break

        control.closeAllDialogs()

        try:
            audio_lang = self.getAvailableAudioStreams()
            if len(audio_lang) > 1:
                try:
                    preferred_audio = int(control.getSetting('general.audio'))
                    audio_int = audio_lang.index(control.lang(preferred_audio))
                    self.setAudioStream(audio_int)
                except:
                    pass
                try:
                    if preferred_audio == 40315:
                        self.setSubtitleStream(1)
                except:
                    pass
        except:
            pass

        if self.media_type == 'movie':
            return self.onWatchedPercent()

        if control.getSetting('smartplay.skipintrodialog') == 'true':
            while self.isPlaying():
                time_ = int(self.getTime())
                if time_ > 240:
                    break
                elif time_ >= 1:
                    PlayerDialogs()._show_skip_intro()
                    break
                else:
                    xbmc.sleep(250)

        scrobble = self.onWatchedPercent()

        if control.getSetting('smartplay.playingnextdialog') == 'true':
            endpoint = int(control.getSetting('playingnext.time'))
        else:
            endpoint = False

        if endpoint:
            while self.isPlaying():
                if int(self.getTotalTime()) - int(self.getTime()) <= endpoint:
                    xbmc.executebuiltin('RunPlugin("plugin://plugin.video.kaito/run_player_dialogs")')
                    break
                else:
                    xbmc.sleep(1000)

class PlayerDialogs(xbmc.Player):

    def __init__(self):
        super(PlayerDialogs, self).__init__()
        self._min_time = 30
        self.playing_file = self.getPlayingFile()

    def display_dialog(self):

        if playList.size() == 0 or playList.getposition() == (playList.size() - 1):
            return

        target = self._show_playing_next

        if self.playing_file != self.getPlayingFile():
            return

        if not self.isPlayingVideo():
            return

        if not self._is_video_window_open():
            return

        target()

    @staticmethod
    def _still_watching_calc():
        return False

    def _show_playing_next(self):
        from resources.lib.windows.playing_next import PlayingNext

        PlayingNext(*('playing_next.xml', ADDON_PATH),
                    actionArgs=self._get_next_item_args()).doModal()

    def _show_skip_intro(self):
        from resources.lib.windows.skip_intro import SkipIntro

        SkipIntro(*('skip_intro.xml', ADDON_PATH),
                    actionArgs={'item_type': 'skip_intro'}).doModal()

    def _show_still_watching(self):
        return True

    @staticmethod
    def _get_next_item_args():
        current_position = playList.getposition()
        _next_info = playList[current_position + 1]
        next_info = {}
        next_info['thumb'] = _next_info.getArt('thumb')
        next_info['name'] = _next_info.getLabel()
        next_info['playnext'] = True
        return next_info

    @staticmethod
    def _is_video_window_open():

        if kodiGui.getCurrentWindowId() != 12005:
            return False
        return True

def cancelPlayback():
    playList.clear()
    xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())

def _prefetch_play_link(link):
    if callable(link):
        link = link()

    if not link:
        return None

    linkInfo = http.head_request(link);
    if linkInfo.status_code != 200:
        raise Exception('could not resolve %s. status_code=%d' %
                        (link, linkInfo.status_code))
    return {
        "url": linkInfo.url,
        "headers": linkInfo.headers,
    }

def play_source(link, anilist_id=None, watchlist_update=None, build_playlist=None, episode=None, filter_lang=None, rescrape=False):
    linkInfo = _prefetch_play_link(link)
    if not linkInfo:
        cancelPlayback()
        return

    item = xbmcgui.ListItem(path=linkInfo['url'])

    if rescrape:
        episode_info = build_playlist(anilist_id, '', filter_lang, rescrape=True)[episode - 1]
        item.setInfo('video', infoLabels=episode_info['info'])
        item.setArt(episode_info['image'])

    if 'Content-Type' in linkInfo['headers']:
        item.setProperty('mimetype', linkInfo['headers']['Content-Type'])

    # Run any mimetype hook
    item = hook_mimetype.trigger(linkInfo['headers']['Content-Type'], item)
    xbmcplugin.setResolvedUrl(HANDLE, True, item)
    watchlistPlayer().handle_player(anilist_id, watchlist_update, build_playlist, episode, filter_lang)

@hook_mimetype('application/dash+xml')
def _DASH_HOOK(item):
    import inputstreamhelper
    is_helper = inputstreamhelper.Helper('mpd')
    if is_helper.check_inputstream():
        item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
        item.setProperty('inputstream.adaptive.manifest_type',
                             'mpd')
        item.setContentLookup(False)
    else:
        raise Exception("InputStream Adaptive is not supported.")

    return item

@hook_mimetype('application/vnd.apple.mpegurl')
def _HLS_HOOK(item):
    import inputstreamhelper
    is_helper = inputstreamhelper.Helper('hls')
    if is_helper.check_inputstream():
        item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
        item.setProperty('inputstream.adaptive.manifest_type',
                             'hls')
        item.setContentLookup(False)
    else:
        raise Exception("InputStream Adaptive is not supported.")

    return item
