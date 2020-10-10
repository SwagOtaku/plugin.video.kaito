import ast
from ui import control
from ui.router import route
from WatchlistFlavor import WatchlistFlavor
from ui import database

_BROWSER = None
def set_browser(browser):
    global _BROWSER
    _BROWSER = browser

def get_anilist_res(mal_id):
    from AniListBrowser import AniListBrowser
    return AniListBrowser().get_mal_to_anilist(mal_id)

def get_auth_dialog(flavor):
    from resources.lib.windows.wlf_auth import WatchlistFlavorAuth

    auth = WatchlistFlavorAuth(*('wlf_auth_%s.xml' % flavor, control.ADDON_PATH),
                                    flavor=flavor).doModal()

    if auth:
        return WatchlistFlavor.login_request(flavor)
    else:
        return

@route('watchlist_login/*')
def WL_LOGIN(payload, params):
    if params:
        return get_auth_dialog(payload)
        
    return WatchlistFlavor.login_request(payload)

@route('watchlist_logout/*')
def WL_LOGOUT(payload, params):
    return WatchlistFlavor.logout_request(payload)

@route('watchlist/*')
def WATCHLIST(payload, params):
    return control.draw_items(WatchlistFlavor.watchlist_request(payload))

@route('watchlist_status_type/*')
def WATCHLIST_STATUS_TYPE(payload, params):
    flavor, status = payload.rsplit("/")
    return control.draw_items(WatchlistFlavor.watchlist_status_request(flavor, status))

@route('watchlist_status_type_pages/*')
def WATCHLIST_STATUS_TYPE_PAGES(payload, params):
    flavor, status, offset, page = payload.rsplit("/")
    return control.draw_items(WatchlistFlavor.watchlist_status_request_pages(flavor, status, offset, int(page)))

@route('watchlist_query/*')
def WATCHLIST_QUERY(payload, params):
    anilist_id, mal_id = payload.rsplit("/")
    anime_general, content_type = _BROWSER.get_anime_init(anilist_id)
    return control.draw_items(anime_general, content_type)

@route('watchlist_to_ep/*')
def WATCHLIST_TO_EP(payload, params):
    mal_id, kitsu_id, eps_watched = payload.rsplit("/")

    if not mal_id:
        return []

    show_meta = database.get_show_mal(mal_id)

    if not show_meta:
        show_meta = get_anilist_res(mal_id)

    anilist_id = show_meta['anilist_id']
    kodi_meta = ast.literal_eval(show_meta['kodi_meta'])
    kodi_meta['eps_watched'] = eps_watched
    database.update_kodi_meta(anilist_id, kodi_meta)

    if kitsu_id:
        if not show_meta['kitsu_id']:
            database.add_mapping_id(anilist_id, 'kitsu_id', kitsu_id)

    anime_general, content_type = _BROWSER.get_anime_init(anilist_id)
    return control.draw_items(anime_general, content_type)

@route('watchlist_to_movie/*')
def WATCHLIST_QUERY(payload, params):
    mal_id = payload
    show_meta = database.get_show_mal(mal_id)

    if not show_meta:
        show_meta = get_anilist_res(mal_id)

    anilist_id = show_meta['anilist_id']
    sources = _BROWSER.get_sources(anilist_id, '1', 'movie')
    _mock_args = {'anilist_id': anilist_id}
    from resources.lib.windows.source_select import SourceSelect

    link = SourceSelect(*('source_select.xml', control.ADDON_PATH),
                        actionArgs=_mock_args, sources=sources).doModal()

    control.play_source(link)

def watchlist_update(anilist_id, episode):
    flavor = WatchlistFlavor.get_update_flavor()
    if not flavor:
        return

    return WatchlistFlavor.watchlist_update_request(anilist_id, episode)

def add_watchlist(items):
    flavors = WatchlistFlavor.get_enabled_watchlists()
    if not flavors:
        return

    for flavor in flavors:
        items.insert(0, (
            "%s's %s" % (flavor.username, flavor.title),
            "watchlist/%s" % flavor.flavor_name,
            flavor.image,
        ))

