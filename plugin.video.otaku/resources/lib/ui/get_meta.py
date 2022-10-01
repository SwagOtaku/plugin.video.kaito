from resources.lib.ui import database
from resources.lib.indexers.trakt import TRAKTAPI
from resources.lib.indexers.fanart import FANARTAPI
from resources.lib.indexers.tmdb import TMDBAPI
import threading


def collect_meta(anime_list):
    threads = []
    for anime in anime_list:
        if 'media' in anime.keys():
            anime = anime.get('media')
        anilist_id = anime.get('id')
        show_meta = database.get_show_meta(anilist_id)
        if not show_meta:
            name = anime.get('title').get('english')
            if name is None:
                name = anime.get('title').get('romaji')
            mtype = 'movies' if anime.get('format') == 'MOVIE' else 'tv'
            threads.append(threading.Thread(target=__get_meta, args=(anilist_id, name, mtype)))
    [i.start() for i in threads]
    [i.join() for i in threads]
    return


def __get_meta(anilist_id, name, mtype='tv'):
    res = TRAKTAPI().get_trakt(name, mtype)
    if res:
        meta_ids = res.get('ids')
        meta = FANARTAPI().getArt(meta_ids, mtype)
        if not meta:
            meta = TMDBAPI().getArt(meta_ids, mtype)
        elif 'fanart' not in meta.keys():
            meta2 = TMDBAPI().getArt(meta_ids, mtype)
            if meta2.get('fanart'):
                meta.update({'fanart': meta2.get('fanart')})
        database._update_show_meta(anilist_id, meta_ids, meta)
    return
