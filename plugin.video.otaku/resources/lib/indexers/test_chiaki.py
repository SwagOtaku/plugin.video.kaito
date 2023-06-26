from unittest import TestCase
class Test(TestCase):
    def test_get_all_anime(self):
        from resources.lib.indexers import chiaki
        from resources.lib.AniListBrowser import AniListBrowser
        a = AniListBrowser()
        video_data = chiaki.get_all_anime(35062)

        for x, item in enumerate(video_data):
            item_list = item['url'].split("/")[1:]
            if len(item_list) == 4:
                mal_id = item_list[3]
                img = a.get_poster(mal_id, 0)
                item_list[x]['image'] = img['data']['Media']['coverImage']['extraLarge']
                breakpoint()

        if len(video_data) == 0:
            self.fail()