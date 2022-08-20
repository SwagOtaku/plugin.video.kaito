import sys, xbmc

if __name__ == '__main__':

    item = sys.listitem

    path = item.getPath()
    plugin = 'plugin://plugin.video.kaito/'
    path = path.split(plugin, 1)[1]

    xbmc.executebuiltin('ActivateWindow(Videos,plugin://plugin.video.kaito/find_similar/%s)'
                        % path)
