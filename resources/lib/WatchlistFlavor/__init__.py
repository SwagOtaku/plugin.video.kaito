from resources.lib.ui import control
from resources.lib.WatchlistFlavor.WatchlistFlavorBase import WatchlistFlavorBase
from resources.lib.WatchlistFlavor import AniList  # noQA
from resources.lib.WatchlistFlavor import Kitsu  # noQA
from resources.lib.WatchlistFlavor import MyAnimeList  # noQA


class WatchlistFlavor(object):
    __LOGIN_KEY = "addon.login"
    __LOGIN_FLAVOR_KEY = "%s.flavor" % __LOGIN_KEY

    __SELECTED = None

    def __init__(self):
        raise Exception("Static Class should not be created")

    @staticmethod
    def get_enabled_watchlists():
        enabled_watchlists = []
        if control.myanimelist_enabled():
            enabled_watchlists.append(WatchlistFlavor.__instance_flavor('mal'))
        if control.kitsu_enabled():
            enabled_watchlists.append(WatchlistFlavor.__instance_flavor('kitsu'))
        if control.anilist_enabled():
            enabled_watchlists.append(WatchlistFlavor.__instance_flavor('anilist'))

        return enabled_watchlists

    @staticmethod
    def get_update_flavor():
        selected = control.watchlist_to_update()
        if not selected:
            return None

        if not WatchlistFlavor.__SELECTED:
            WatchlistFlavor.__SELECTED = \
                WatchlistFlavor.__instance_flavor(selected)

        return WatchlistFlavor.__SELECTED

    @staticmethod
    def get_active_flavor():
        selected = control.getSetting(WatchlistFlavor.__LOGIN_FLAVOR_KEY)
        if not selected:
            return None

        if not WatchlistFlavor.__SELECTED:
            WatchlistFlavor.__SELECTED = \
                WatchlistFlavor.__instance_flavor(selected)

        return WatchlistFlavor.__SELECTED

    @staticmethod
    def watchlist_request(name):
        return WatchlistFlavor.__instance_flavor(name).watchlist()

    @staticmethod
    def watchlist_status_request(name, status, next_up):
        return WatchlistFlavor.__instance_flavor(name).get_watchlist_status(status, next_up)

    @staticmethod
    def watchlist_status_request_pages(name, status, next_up, offset, page):
        return WatchlistFlavor.__instance_flavor(name).get_watchlist_status(status, next_up, offset, page)

    @staticmethod
    def watchlist_anime_entry_request(name, anilist_id):
        return WatchlistFlavor.__instance_flavor(name).get_watchlist_anime_entry(anilist_id)

    @staticmethod
    def watchlist_update_request(anilist_id, episode):
        return WatchlistFlavor.get_update_flavor().watchlist_update(anilist_id, episode)

    @staticmethod
    def login_request(flavor):
        if not WatchlistFlavor.__is_flavor_valid(flavor):
            raise Exception("Invalid flavor %s" % flavor)

        flavor_class = WatchlistFlavor.__instance_flavor(flavor)
        login_ts = ''  # int(time())

        return WatchlistFlavor.__set_login(flavor,
                                           flavor_class.login(),
                                           str(login_ts)
                                           )

    @staticmethod
    def logout_request(flavor):
        control.setSetting('%s.userid' % flavor, '')
        control.setSetting('%s.authvar' % flavor, '')
        control.setSetting('%s.token' % flavor, '')
        control.setSetting('%s.refresh' % flavor, '')
        control.setSetting('%s.username' % flavor, '')
        control.setSetting('%s.password' % flavor, '')
        control.setSetting('%s.sort' % flavor, '')
        control.setSetting('%s.titles' % flavor, '')
        return control.refresh()

    @staticmethod
    def __get_flavor_class(name):
        for flav in WatchlistFlavorBase.__subclasses__():
            if flav.name() == name:
                return flav
        return None

    @staticmethod
    def __is_flavor_valid(name):
        return WatchlistFlavor.__get_flavor_class(name) is not None

    @staticmethod
    def __instance_flavor(name):
        user_id = control.getSetting('%s.userid' % name)
        auth_var = control.getSetting('%s.authvar' % name)
        token = control.getSetting('%s.token' % name)
        refresh = control.getSetting('%s.refresh' % name)
        username = control.getSetting('%s.username' % name)
        password = control.getSetting('%s.password' % name)
        sort = control.getSetting('%s.sort' % name)
        title_lang = control.getSetting('%s.titles' % name)

        flavor_class = WatchlistFlavor.__get_flavor_class(name)
        return flavor_class(auth_var, username, password, user_id, token, refresh, sort, title_lang)

    @staticmethod
    def __set_login(flavor, res, login_ts):
        if not res:
            return control.ok_dialog('Login', 'Incorrect username or password')

        for _id, value in list(res.items()):
            control.setSetting('%s.%s' % (flavor, _id), value)

        control.refresh()
        return control.ok_dialog('Login', 'Success')
