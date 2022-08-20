import sys, xbmc

if __name__ == '__main__':

    item = sys.listitem

    path = item.getPath()
    plugin = 'plugin://plugin.video.kaito/'
    path = path.split(plugin, 1)[1]

    xbmc.executebuiltin('XBMC.Container.Update(plugin://plugin.video.kaito/season_correction/%s)'
                        % path)
