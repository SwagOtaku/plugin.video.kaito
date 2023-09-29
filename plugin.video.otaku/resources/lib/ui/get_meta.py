import threading

from resources.lib.indexers.fanart import FANARTAPI
from resources.lib.indexers.tmdb import TMDBAPI
from resources.lib.indexers.trakt import TRAKTAPI
from resources.lib.indexers.enime import ENIMEAPI
from resources.lib.ui import database


def collect_meta(anime_list):
    threads = []
    for anime in anime_list:
        if 'media' in anime.keys():
            anime = anime.get('media')
        anilist_id = anime.get('id')
        show_meta = database.get_show_meta(anilist_id)
        if not show_meta:
            name = anime['title'].get('english')
            if name is None:
                name = anime['title'].get('romaji')
            mtype = 'movies' if anime.get('format') == 'MOVIE' else 'tv'
            if anime.get('format') == 'ONA' and anime.get('episodes') == 1:
                mtype = 'movies'
            year = anime['startDate'].get('year')
            threads.append(threading.Thread(target=__get_meta, args=(anilist_id, name, mtype, year)))
    [i.start() for i in threads]
    [i.join() for i in threads]


def __get_meta(anilist_id, name, mtype='tv', year=''):
    res = ENIMEAPI().get_anilist_mapping(anilist_id)
    if isinstance(res, dict):
        meta_ids = res.get('mappings')
        if 'themoviedb' in meta_ids.keys() or 'thetvdb' in meta_ids.keys():
            update_meta(anilist_id, meta_ids, mtype)
        else:
            __trakt_fallback(anilist_id, name, mtype=mtype, year=year)
    else:
        __trakt_fallback(anilist_id, name, mtype=mtype, year=year)


def __trakt_fallback(anilist_id, name, mtype='tv', year=''):
    resp = TRAKTAPI().get_trakt(name, mtype=mtype, year=year)
    if resp:
        meta_ids = resp.get('ids')
        update_meta(anilist_id, meta_ids, mtype)


def update_meta(anilist_id, meta_ids={}, mtype='tv'):
    meta = FANARTAPI().getArt(meta_ids, mtype)
    if not meta:
        meta = TMDBAPI().getArt(meta_ids, mtype)
    elif 'fanart' not in meta.keys():
        meta2 = TMDBAPI().getArt(meta_ids, mtype)
        if meta2.get('fanart'):
            meta['fanart'] = meta2['fanart']
    database.update_show_meta(anilist_id, meta_ids, meta)
