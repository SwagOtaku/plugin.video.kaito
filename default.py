# -*- coding: utf-8 -*-
from resources.lib.ui import control
from resources.lib.ui import player
from resources.lib.ui import database
from resources.lib.ui.globals import g
from resources.lib.ui.router import on_param, route, router_process
from resources.lib.KaitoBrowser import KaitoBrowser
from resources.lib.AniListBrowser import AniListBrowser
from resources.lib.WatchlistIntegration import set_browser, add_watchlist, watchlist_update
import ast
import sys

g.init_globals(sys.argv)

MENU_ITEMS = [
    (g.lang(30001), "anilist_airing", ''),
    (g.lang(30002), "airing_dub", ''),
    (g.lang(30003), "latest", ''),
    (g.lang(30004), "latest_dub", ''),
    (g.lang(30005), "anilist_trending", ''),
    (g.lang(30006), "anilist_popular", ''),
    (g.lang(30007), "anilist_upcoming", ''),
    (g.lang(30008), 'anilist_all_time_popular', ''),
    (g.lang(30009), "anilist_genres", ''),
    (g.lang(30010), "search_history", ''),
    (g.lang(30011), "tools", ''),
]

_TITLE_LANG = g.get_setting("titlelanguage")

_BROWSER = KaitoBrowser()

_ANILIST_BROWSER = AniListBrowser(_TITLE_LANG)

def _add_last_watched():
    anilist_id = g.get_setting("addon.last_watched")
    if not anilist_id:
        return

    try:
        last_watched = ast.literal_eval(database.get_show(anilist_id)['kodi_meta'])
    except:
        return

    MENU_ITEMS.insert(0, (
        "%s[I]%s[/I]" % (g.lang(30000), control.decode_py2(last_watched['name'])),
        "animes/%s/null/" % anilist_id,
        last_watched['poster']
    ))

def get_animes_contentType(seasons=None):
    contentType = g.get_setting("contenttype.episodes")
    if seasons and seasons[0]['is_dir']:
        contentType = g.get_setting("contenttype.seasons")

    return contentType

#Will be called at handle_player
def on_percent():
    return int(g.get_setting('watchlist.percent'))

#Will be called when player is stopped in the middle of the episode
def on_stopped():
    return control.yesno_dialog(g.lang(30200), g.lang(30201), g.lang(30202))

#Will be called on genre page
def genre_dialog(genre_display_list):
    return control.multiselect_dialog(g.lang(30009), genre_display_list)

@route('season_correction/*')
def seasonCorrection(payload, params):
    anilist_id, mal_id, filter_lang = payload.split("/")[1:]
    trakt = _BROWSER.search_trakt_shows(anilist_id)
    return g.draw_items(trakt)

@route('season_correction_database/*')
def seasonCorrectionDatabase(payload, params):
    show_id, meta_ids = payload.rsplit("/")
    clean_show = _BROWSER.clean_show(show_id, meta_ids)
    trakt, content_type = _BROWSER.get_anime_trakt(show_id, True)
    return g.draw_items(trakt, content_type)

@route('find_similar/*')
def FIND_SIMILAR(payload, params):
    anilist_id, mal_id, filter_lang = payload.split("/")[1:]
    return g.draw_items(_ANILIST_BROWSER.get_recommendation(anilist_id))

@route('authAllDebrid')
def authAllDebrid(payload, params):
    from resources.lib.debrid.all_debrid import AllDebrid
    AllDebrid().auth()

@route('authRealDebrid')
def authRealDebrid(payload, params):
    from resources.lib.debrid.real_debrid import RealDebrid
    RealDebrid().auth()

@route('authPremiumize')
def authPremiumize(payload, params):
    from resources.lib.debrid.premiumize import Premiumize
    Premiumize().auth()

@route('settings')
def SETTINGS(payload, params):
    return control.settingsMenu();

@route('clear_cache')
def CLEAR_CACHE(payload, params):
    database.cache_clear()
    return control.clear_cache();

@route('clear_torrent_cache')
def CLEAR_TORRENT_CACHE(payload, params):
    return database.torrent_cache_clear()

@route('rebuild_database')
def REBUILD_DATABASE(payload, params):
    from resources.lib.ui.database_sync import AnilistSyncDatabase
    AnilistSyncDatabase().re_build_database()

@route('wipe_addon_data')
def WIPE_ADDON_DATA(payload, params):
    from resources.lib.ui import maintenance
    maintenance.wipe_install()

@route('toggleLanguageInvoker')
def TOGGLE_LANGUAGE_INVOKER(payload, params):
    from resources.lib.ui.maintenance import toggle_reuselanguageinvoker
    toggle_reuselanguageinvoker()    

@route('animes/*')
def ANIMES_PAGE(payload, params):
    anilist_id, mal_id, filter_lang = payload.rsplit("/")
    anime_general, content = _BROWSER.get_anime_init(anilist_id, filter_lang)
    return g.draw_items(anime_general, content)

@route('animes_trakt/*')
def ANIMES_TRAKT(payload, params):
    show_id, season = payload.rsplit("/")
    database._update_season(show_id, season)
    return g.draw_items(_BROWSER.get_trakt_episodes(show_id, season), 'episodes')

@route('run_player_dialogs')
def RUN_PLAYER_DIALOGS(payload, params):
    from resources.lib.ui.player import PlayerDialogs
    try:
        PlayerDialogs().display_dialog()
    except:
        import traceback
        traceback.print_exc()

@route('test')
def TEST(payload, params):
    return

@route('anilist_airing')
def ANILIST_AIRING(payload, params):
    airing = _ANILIST_BROWSER.get_airing()
    from resources.lib.windows.anichart import Anichart

    anime = Anichart(*('anichart.xml', g.ADDON_DATA_PATH),
                        get_anime=_BROWSER.get_anime_init, anime_items=airing).doModal()

    if not anime:
        anime = [[], 'tvshows']

    anime, content_type = anime

    return g.draw_items(anime, content_type)

@route('airing_dub')
def AIRING_DUB(payload, params):
    return g.draw_items(_BROWSER.get_airing_dub())

@route('latest')
def LATEST(payload, params):
    return g.draw_items(_BROWSER.get_latest(g.real_debrid_enabled(), g.premiumize_enabled()), 'episodes')

@route('latest_dub')
def LATEST_DUB(payload, params):
    return g.draw_items(_BROWSER.get_latest_dub(g.real_debrid_enabled(), g.premiumize_enabled()), 'episodes')

@route('anilist_trending')
def ANILIST_TRENDING(payload, params):
    return g.draw_items(_ANILIST_BROWSER.get_trending())

@route('anilist_trending/*')
def ANILIST_TRENDING_PAGES(payload, params):
    return g.draw_items(_ANILIST_BROWSER.get_trending(int(payload)))

@route('anilist_popular')
def ANILIST_POPULAR(payload, params):
    return g.draw_items(_ANILIST_BROWSER.get_popular())

@route('anilist_popular/*')
def ANILIST_POPULAR_PAGES(payload, params):
    return g.draw_items(_ANILIST_BROWSER.get_popular(int(payload)))

@route('anilist_upcoming')
def ANILIST_POPULAR(payload, params):
    return g.draw_items(_ANILIST_BROWSER.get_upcoming())

@route('anilist_upcoming/*')
def ANILIST_POPULAR_PAGES(payload, params):
    return g.draw_items(_ANILIST_BROWSER.get_upcoming(int(payload)))

@route('anilist_all_time_popular')
def ANILIST_ALL_TIME_POPULAR(payload, params):
    return g.draw_items(_ANILIST_BROWSER.get_all_time_popular())

@route('anilist_all_time_popular/*')
def ANILIST_ALL_TIME_POPULAR_PAGES(payload, params):
    return g.draw_items(_ANILIST_BROWSER.get_all_time_popular(int(payload)))

@route('anilist_genres')
def ANILIST_GENRES(payload, params):
    return g.draw_items(_ANILIST_BROWSER.get_genres(genre_dialog))

@route('anilist_genres/*')
def ANILIST_GENRES_PAGES(payload, params):
    genres, tags, page = payload.split("/")[-3:]
    return g.draw_items(_ANILIST_BROWSER.get_genres_page(genres, tags, int(page)))

@route('search_history')
def SEARCH_HISTORY(payload, params):
    history = database.getSearchHistory('show')
    if "Yes" in g.get_setting('searchhistory') :
        return g.draw_items(_BROWSER.search_history(history), contentType=g.get_setting("contenttype.menu"))
    else :
        return SEARCH(payload,params)

@route('clear_history')
def CLEAR_HISTORY(payload, params):
    database.clearSearchHistory()
    return

@route('search')
def SEARCH(payload, params):
    query = control.keyboard(g.lang(30010))
    if not query:
        return False

    # TODO: Better logic here, maybe move functionatly into router?
    if "Yes" in g.get_setting('searchhistory') :
        database.addSearchHistory(query, 'show')
        history = database.getSearchHistory('show')

    return g.draw_items(_ANILIST_BROWSER.get_search(query))

@route('search/*')
def SEARCH_PAGES(payload, params):
    query, page = payload.rsplit("/", 1)
    return g.draw_items(_ANILIST_BROWSER.get_search(query, int(page)))

@route('play_latest/*')
def PLAY(payload, params):
    debrid_provider, hash_ = payload.rsplit('/')
    link = _BROWSER.get_latest_sources(debrid_provider, hash_)
    player.play_source(link)

@route('play_movie/*')
def PLAY_MOVIE(payload, params):
    anilist_id, episode, filter_lang = payload.rsplit("/")
    sources = _BROWSER.get_sources(anilist_id, episode, filter_lang, 'movie')

    _mock_args = {'anilist_id': anilist_id}

    if g.get_setting('general.playstyle.movie') == '1' or params.get('source_select'):

        from resources.lib.windows.source_select import SourceSelect

        link = SourceSelect(*('source_select.xml', g.ADDON_DATA_PATH),
                            actionArgs=_mock_args, sources=sources).doModal()
    else:
        from resources.lib.windows.resolver import Resolver

        resolver = Resolver(*('resolver.xml', g.ADDON_DATA_PATH),
                            actionArgs=_mock_args)

        link = resolver.doModal(sources, {}, False)

    player.play_source(link,
                        anilist_id,
                        watchlist_update,
                        None,
                        int(episode))

@route('play_gogo/*')
def PLAY_GOGO(payload, params):
    slug, episode = payload.rsplit('/')
    from resources.lib.pages import gogoanime
    sources = gogoanime.sources()._process_gogo(slug, '', episode)

    _mock_args = {}
    from resources.lib.windows.source_select import SourceSelect

    link = SourceSelect(*('source_select.xml', g.ADDON_DATA_PATH),
                        actionArgs=_mock_args, sources=sources).doModal()

    player.play_source(link)

@route('play/*')
def PLAY(payload, params):
    anilist_id, episode, filter_lang = payload.rsplit("/")
    sources = _BROWSER.get_sources(anilist_id, episode, filter_lang, 'show')
    _mock_args = {"anilist_id": anilist_id}

    if g.get_setting('general.playstyle.episode') == '1' or params.get('source_select'):

        from resources.lib.windows.source_select import SourceSelect

        link = SourceSelect(*('source_select.xml', g.ADDON_DATA_PATH),
                            actionArgs=_mock_args, sources=sources).doModal()
    else:
        from resources.lib.windows.resolver import Resolver

        resolver = Resolver(*('resolver.xml', g.ADDON_DATA_PATH),
                            actionArgs=_mock_args)

        link = resolver.doModal(sources, {}, False)

    player.play_source(link,
                        anilist_id,
                        watchlist_update,
                        _BROWSER.get_episodeList,
                        int(episode),
                        filter_lang)

@route('rescrape_play/*')
def RESCRAPE_PLAY(payload, params):
    anilist_id, episode, filter_lang = payload.rsplit("/")
    sources = _BROWSER.get_sources(anilist_id, episode, filter_lang, 'show', True)
    _mock_args = {"anilist_id": anilist_id}

    from resources.lib.windows.source_select import SourceSelect

    link = SourceSelect(*('source_select.xml', g.ADDON_DATA_PATH),
                        actionArgs=_mock_args, sources=sources, anilist_id=anilist_id, rescrape=True).doModal()

    player.play_source(link,
                        anilist_id,
                        watchlist_update,
                        _BROWSER.get_episodeList,
                        int(episode),
                        filter_lang,
                        rescrape=True)

@route('tools')
def TOOLS_MENU(payload, params):
    TOOLS_ITEMS = [
        (g.lang(30020), "settings", ''),
        (g.lang(30021), "clear_cache", ''),
        (g.lang(30022), "clear_torrent_cache", ''),
        (g.lang(30023), "clear_history", ''),
        (g.lang(30026), "rebuild_database", ''),
        (g.lang(30024), "wipe_addon_data", ''),
        ]

    return g.draw_items(
        [g.allocate_item(name, url, False, image) for name, url, image in TOOLS_ITEMS],
        contentType=g.get_setting("contenttype.menu"),
    )

@route('')
def LIST_MENU(payload, params):
    return g.draw_items(
        [g.allocate_item(name, url, True, image) for name, url, image in MENU_ITEMS],
        contentType=g.get_setting("contenttype.menu"),
    )

set_browser(_BROWSER)
_add_last_watched()
add_watchlist(MENU_ITEMS)
router_process(g.PATH[1:], g.REQUEST_PARAMS)