from unittest import TestCase
class Test(TestCase):
    def test_get_all_anime(self):
        #35062
        from resources.lib.ui import control
        from resources.lib.AniListBrowser import AniListBrowser
        a = AniListBrowser()

        control.draw_items(a.get_watch_order(35062))
        self.fail()