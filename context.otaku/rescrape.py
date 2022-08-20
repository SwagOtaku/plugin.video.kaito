import sys
import xbmc

if __name__ == '__main__':
    item = sys.listitem
    message = item.getLabel()
    path = item.getPath()

    path = path.replace('play', 'rescrape_play')
    path += '?=null'

    xbmc.executebuiltin('PlayMedia(%s)' % path)
