import pickle

from resources.lib.ui import control, database
from resources.lib.ui.router import route
from resources.lib.WatchlistFlavor import WatchlistFlavor

# define a global variable _BROWSER, initially set to None
_BROWSER = None


# function that sets the _BROWSER global variable
def set_browser(browser):
    global _BROWSER
    _BROWSER = browser


# function that gets anime metadata from AniList using MAL ID as input
def get_anilist_res(mal_id):
    # get title language preference from Kodi settings
    title_lang = control.getSetting("titlelanguage")
    # import and use the AniListBrowser class to retrieve metadata
    from resources.lib.AniListBrowser import AniListBrowser
    # return the retrieved data
    return AniListBrowser(title_lang).get_mal_to_anilist(mal_id)


# function that returns an authentication dialog for the user to enter login credentials
# flavor parameter specifies which type of authentication dialog to return
def get_auth_dialog(flavor):
    import sys
    # import the wlf_auth module, which contains authentication dialogs for various platforms
    from resources.lib.windows import wlf_auth
    # get the current platform name
    platform = sys.platform
    # if platform is Linux, use AltWatchlistFlavorAuth authentication dialog
    if 'linux' in platform:
        auth = wlf_auth.AltWatchlistFlavorAuth(flavor).set_settings()
    # if not Linux, use WatchlistFlavorAuth authentication dialog
    else:
        auth = wlf_auth.WatchlistFlavorAuth(*('wlf_auth_%s.xml' % flavor, control.ADDON_PATH),
                                            flavor=flavor).doModal()
    # check if authentication was successful
    if auth:
        return WatchlistFlavor.login_request(flavor)
    else:
        return


# route decorator for login page
@route('watchlist_login/*')
def WL_LOGIN(payload, params):
    # if payload contains additional parameters, return corresponding authentication dialog
    if params:
        return get_auth_dialog(payload)
    # else, return login request for flavor specified in payload
    return WatchlistFlavor.login_request(payload)


# route decorator for logout page
@route('watchlist_logout/*')
def WL_LOGOUT(payload, params):
    # return logout request for specified flavor
    return WatchlistFlavor.logout_request(payload)


# route decorator for watchlist page
@route('watchlist/*')
def WATCHLIST(payload, params):
    # return watchlist request for specified flavor
    return control.draw_items(WatchlistFlavor.watchlist_request(payload), contentType="addons")


# route decorator for watchlist status/type page
@route('watchlist_status_type/*')
def WATCHLIST_STATUS_TYPE(payload, params):
    # split the payload into flavor and status/type parameters
    flavor, status = payload.rsplit("/")
    # define context menu
    draw_cm = ('Remove from Watchlist', 'remove_from_watchlist')
    # return watchlist status/type request with context menu
    return control.draw_items(WatchlistFlavor.watchlist_status_request(flavor, status, params), draw_cm=draw_cm)


# route decorator for watchlist status/type pages
@route('watchlist_status_type_pages/*')
def WATCHLIST_STATUS_TYPE_PAGES(payload, params):
    # split the payload into flavor, status/type, offset, and page parameters
    flavor, status, offset, page = payload.rsplit("/")
    # define context menu
    draw_cm = ('Remove from Watchlist', 'remove_from_watchlist')
    # return watchlist status/type request with context menu
    return control.draw_items(WatchlistFlavor.watchlist_status_request_pages(flavor, status, params, offset, int(page)), draw_cm=draw_cm)


# route decorator for query page
@route('watchlist_query/*')
def WATCHLIST_QUERY(payload, params):
    # split the payload into AniList ID, MAL ID, and episodes watched parameters
    anilist_id, mal_id, eps_watched = payload.rsplit("/")
    # get show metadata from local database using AniList ID
    show_meta = database.get_show(anilist_id)
    # if show metadata not found in database, retrieve from AniList
    if not show_meta:
        from resources.lib.AniListBrowser import AniListBrowser
        show_meta = AniListBrowser().get_anilist(anilist_id)
    # unpickle Kodi metadata and update episodes watched count
    kodi_meta = pickle.loads(show_meta['kodi_meta'])
    kodi_meta['eps_watched'] = eps_watched
    # update Kodi metadata in local database
    database.update_kodi_meta(anilist_id, kodi_meta)
    # use _BROWSER to initialize anime data and return it
    anime_general, content_type = _BROWSER.get_anime_init(anilist_id)
    return control.draw_items(anime_general, content_type)


# route decorator for watchlist-to-ep page
@route('watchlist_to_ep/*')
def WATCHLIST_TO_EP(payload, params):
    # split the payload into MAL ID, kitsu ID (if present), and episodes watched parameters
    parts = payload.rsplit("/")
    if len(parts) > 2:
        mal_id, kitsu_id, eps_watched = parts
    else:
        mal_id, eps_watched = parts
        kitsu_id = ''
    # if MAL ID not found in local database, retrieve show metadata from AniList
    if not mal_id:
        return []
    show_meta = database.get_show_mal(mal_id)
    if not show_meta:
        show_meta = get_anilist_res(mal_id)
    # update Kodi metadata with episodes watched count
    anilist_id = show_meta['anilist_id']
    kodi_meta = pickle.loads(show_meta['kodi_meta'])
    kodi_meta['eps_watched'] = eps_watched
    database.update_kodi_meta(anilist_id, kodi_meta)
    # if kitsu ID provided and not already in local database, add to mapping table
    if kitsu_id:
        if not show_meta['kitsu_id']:
            database.add_mapping_id(anilist_id, 'kitsu_id', kitsu_id)
    # use _BROWSER to initialize anime data and return it
    anime_general, content_type = _BROWSER.get_anime_init(anilist_id)
    return control.draw_items(anime_general, content_type)


# route decorator for watchlist-to-movie page
@route('watchlist_to_movie/*')
def WATCHLIST_TO_MOVIE(payload, params):
    # if additional parameters included, use AniList ID to retrieve show metadata
    if params:
        anilist_id = params['anilist_id']
        show_meta = database.get_show(anilist_id)
        if not show_meta:
            from resources.lib.AniListBrowser import AniListBrowser
            show_meta = AniListBrowser().get_anilist(anilist_id)
    # if no additional parameters, use MAL ID to retrieve show metadata
    else:
        mal_id = payload
        show_meta = database.get_show_mal(mal_id)
        if not show_meta:
            show_meta = get_anilist_res(mal_id)
        anilist_id = show_meta['anilist_id']
    # get available sources for the movie using _BROWSER
    sources = _BROWSER.get_sources(anilist_id, '1', None, 'movie')
    # create mock arguments for source select dialog
    _mock_args = {'anilist_id': anilist_id}
    # import and use the SourceSelect class to display the source select dialog
    from resources.lib.windows.source_select import SourceSelect
    link = SourceSelect(*('source_select.xml', control.ADDON_PATH),
                        actionArgs=_mock_args, sources=sources).doModal()
    # if subs are present, split them from the link
    subs = []
    if isinstance(link, tuple):
        link, subs = link
    # use the player module to play the selected source with subtitles (if present)
    from resources.lib.ui import player
    player.play_source(link, subs=subs)


# function that updates a show's episode count in the user's watchlist
def watchlist_update(anilist_id, episode):
    flavor = WatchlistFlavor.get_update_flavor()
    if not flavor:
        return
    return WatchlistFlavor.watchlist_update_request(anilist_id, episode)


# function that appends a show to the user's watchlist
def watchlist_append(anilist_id):
    flavor = WatchlistFlavor.get_update_flavor()
    if not flavor:
        return
    return WatchlistFlavor.watchlist_append_request(anilist_id)


# function that removes a show from the user's watchlist
def watchlist_remove(anilist_id):
    flavor = WatchlistFlavor.get_update_flavor()
    if not flavor:
        return
    return WatchlistFlavor.watchlist_remove_request(anilist_id)


# function that adds enabled watchlists to the given items list
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
