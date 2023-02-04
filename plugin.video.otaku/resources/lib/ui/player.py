import sys
import time

from kodi_six import xbmc, xbmcgui, xbmcplugin
from resources.lib.ui import client, control
from six.moves import urllib_parse

try:
    HANDLE = int(sys.argv[1])
except:
    HANDLE = '1'

playList = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
player = xbmc.Player
progressDialog = xbmcgui.DialogProgress()


class hook_mimetype(object):
    __MIME_HOOKS = {}

    @classmethod
    def trigger(cls, mimetype, item):

        if mimetype in cls.__MIME_HOOKS.keys():
            return cls.__MIME_HOOKS[mimetype](item)

        return item

    def __init__(self, mimetype):
        self._type = mimetype

    def __call__(self, func):
        assert self._type not in self.__MIME_HOOKS.keys()
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
        # self.AVStarted = False

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

    # def onAVStarted(self):
    #     self.AVStarted = True

    # def onAVChange(self):
    #     self.AVStarted = True

    def onPlayBackStopped(self):
        playList.clear()

    # def onPlayBackEnded(self):
    #     pass

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

        if int(media_length) != 0:
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

        # for i in range(0, 480):
        #     if self.AVStarted:
        #         break

        control.closeAllDialogs()

        audio_lang = self.getAvailableAudioStreams()
        if len(audio_lang) > 1:
            preferred_audio = control.getSetting('general.audio')
            if len(preferred_audio) == 5:
                preferred_audio = control.lang(int(preferred_audio))
            audio_int = audio_lang.index(preferred_audio)
            self.setAudioStream(audio_int)

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

        _ = self.onWatchedPercent()

        if control.getSetting('smartplay.playingnextdialog') == 'true':
            endpoint = int(control.getSetting('playingnext.time'))
        else:
            endpoint = False

        if endpoint:
            while self.isPlaying():
                if int(self.getTotalTime()) - int(self.getTime()) <= endpoint:
                    # xbmc.executebuiltin('RunPlugin("plugin://plugin.video.otaku/run_player_dialogs")')
                    PlayerDialogs().display_dialog()
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

        PlayingNext(*('playing_next.xml', control.ADDON_PATH),
                    actionArgs=self._get_next_item_args()).doModal()

    def _show_skip_intro(self):
        from resources.lib.windows.skip_intro import SkipIntro

        delay_time = int(control.getSetting("set_delay_time"))
        time.sleep(delay_time)

        SkipIntro(*('skip_intro.xml', control.ADDON_PATH),
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

        if xbmcgui.getCurrentWindowId() != 12005:
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
    url = link
    headers = {}

    if '|' in url:
        url, hdrs = link.split('|')
        headers = dict([item.split('=') for item in hdrs.split('&')])
        for header in headers:
            headers[header] = urllib_parse.unquote_plus(headers[header])

    linkInfo = client.request(url, headers=headers, limit='0', output='extended')
    if linkInfo[1] != '200':
        raise Exception('could not resolve %s. status_code=%s' %
                        (link, linkInfo[1]))
    return {
        "url": link if '|' in link else linkInfo[5],
        "headers": linkInfo[2],
    }


def play_source(link, anilist_id=None, watchlist_update=None, build_playlist=None, episode=None, filter_lang=None, rescrape=False, source_select=False):
    try:
        linkInfo = _prefetch_play_link(link)
        if not linkInfo:
            cancelPlayback()
            return
    except Exception as e:
        cancelPlayback()
        control.ok_dialog('Otaku', str(e))
        return

    item = xbmcgui.ListItem(path=linkInfo['url'])

    if rescrape:
        episode_info = build_playlist(anilist_id, '', filter_lang, rescrape=True)[episode - 1]
        item.setInfo('video', infoLabels=episode_info['info'])
        item.setArt(episode_info['image'])
    elif source_select:
        episode_info = build_playlist(anilist_id, '', filter_lang, sourceselect=True)[episode - 1]
        item.setInfo('video', infoLabels=episode_info['info'])
        item.setArt(episode_info['image'])
        
    if 'Content-Type' in linkInfo['headers'].keys():
        item.setProperty('MimeType', linkInfo['headers']['Content-Type'])
        # Run any mimetype hook
        item = hook_mimetype.trigger(linkInfo['headers']['Content-Type'], item)

    xbmcplugin.setResolvedUrl(HANDLE, True, item)
    watchlistPlayer().handle_player(anilist_id, watchlist_update, build_playlist, episode, filter_lang)


@hook_mimetype('application/dash+xml')
def _DASH_HOOK(item):
    import inputstreamhelper
    is_helper = inputstreamhelper.Helper('mpd')
    if is_helper.check_inputstream():
        if control.getKodiVersion() < 19:
            item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
        else:
            item.setProperty('inputstream', is_helper.inputstream_addon)
        item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        item.setContentLookup(False)
    else:
        raise Exception("InputStream Adaptive is not supported.")

    return item


@hook_mimetype('application/vnd.apple.mpegurl')
def _HLS_HOOK(item):
    stream_url = item.getPath()
    import inputstreamhelper
    is_helper = inputstreamhelper.Helper('hls')
    if is_helper.check_inputstream():
        if control.getKodiVersion() < 19:
            item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
        else:
            item.setProperty('inputstream', is_helper.inputstream_addon)
        if '|' in stream_url:
            stream_url, strhdr = stream_url.split('|')
            item.setProperty('inputstream.adaptive.stream_headers', strhdr)
            item.setPath(stream_url)
        item.setProperty('inputstream.adaptive.manifest_type', 'hls')
        item.setProperty('MimeType', 'application/vnd.apple.mpegurl')
        item.setMimeType('application/vnd.apple.mpegstream_url')
        item.setContentLookup(False)
    else:
        raise Exception("InputStream Adaptive is not supported.")

    return item
