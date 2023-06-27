from unittest import TestCase
class Test(TestCase):
    def test_get_all_anime(self):
        from resources.lib.ui import control
        from resources.lib.AniListBrowser import AniListBrowser
        a = AniListBrowser()
        # r = a.get_relations(157198)
        # if len(r) == 0:
        #     self.fail()
        # r = a.get_recommendations(157198)
        # if len(r) == 0:
        #     self.fail()
        r = a.get_watch_order(35062)

        if len(r) == 0:
            self.fail()
        #control.draw_items(r)
