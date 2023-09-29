import sys
import xbmc

if __name__ == '__main__':
    item = sys.listitem
    path = item.getPath()

    path += '?rescrape=true'

    xbmc.executebuiltin('PlayMedia(%s)' % path)
