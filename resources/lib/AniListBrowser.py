import itertools
import requests
import json
import time
import datetime
import ast
from functools import partial
from ui import utils
from ui import database

class AniListBrowser():
    _URL = "https://graphql.anilist.co"

    def __init__(self, title_key=None):
        if title_key:
            self._TITLE_LANG = self._title_lang(title_key)

    def _title_lang(self, title_key):
        title_lang = {
            "40370": "userPreferred",
            "40371": "english",
            }

        return title_lang[title_key]

    def _handle_paging(self, hasNextPage, base_url, page):
        if not hasNextPage:
            return []

        next_page = page + 1
        name = "Next Page (%d)" %(next_page)
        return [utils.allocate_item(name, base_url % next_page, True, None)]

    def get_popular(self, page=1, format_in=''):
        #TASK: update season, year
        season, year = ["FALL", 2020]
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC"
            }

        if format_in:
            variables['format'] = [format_in.upper()]

        popular = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(popular, "anilist_popular/%d", page)

    def get_trending(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': ["TRENDING_DESC"]
            }

        if format_in:
            variables['format'] = [format_in.upper()]

        trending = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(trending, "anilist_trending/%d", page)

    def get_upcoming(self, page=1, format_in=''):
        #TASK: update season, year
        season, year = ["WINTER", 2021]
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC"
            }

        if format_in:
            variables['format'] = [format_in.upper()]

        upcoming = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(upcoming, "anilist_upcoming/%d", page)

    def get_all_time_popular(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "POPULARITY_DESC"
            }

        if format_in:
            variables['format'] = [format_in.upper()]

        all_time_popular = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(all_time_popular, "anilist_all_time_popular/%d", page)

    def get_airing(self, page=1, format_in=''):
        airing = database.get(self._get_airing, 12, page, format_in)
        return airing

    def _get_airing(self, page=1, format_in=''):
        today = datetime.date.today()
        today_ts = int(time.mktime(today.timetuple()))
        weekStart = today_ts - 86400
        weekEnd = today_ts + (86400*6)

        variables = {
            'weekStart': weekStart,
            'weekEnd': weekEnd,
            'page': page
            }

        if format_in:
            variables['format'] = [format_in.upper()]

        list_ = []

        for i in range(0, 4):
            popular = self.get_airing_res(variables, page)
            list_.append(popular)

            if not popular['pageInfo']['hasNextPage']:
                break

            page += 1
            variables['page'] = page
  
        results = map(self._process_airing_view, list_)
        results = list(itertools.chain(*results))
        return results

    def get_search(self, query, page=1):
        variables = {
            'page': page,
            'search': query,
            'sort': "SEARCH_MATCH",
            'type': "ANIME"
            }

        search = database.get(self.get_search_res, 0.125, variables, page)
        return self._process_anilist_view(search, "search/%s/%%d" % query, page)

    def get_recommendation(self, anilist_id, page=1):
        variables = {
            'page': page,
            'id': anilist_id
            }
        
        recommendation = database.get(self.get_recommendations_res, 0.125, variables, page)
        return self._process_recommendation_view(recommendation, "anichart_popular/%d", page)

    def get_anilist(self, mal_id):
        variables = {
            'id': mal_id,
            'type': "ANIME"
            }

        mal_to_anilist = self.get_anilist_res(variables)
        return self._process_mal_to_anilist(mal_to_anilist)

    def get_mal_to_anilist(self, mal_id):
        variables = {
            'id': mal_id,
            'type': "ANIME"
            }

        mal_to_anilist = self.get_mal_to_anilist_res(variables)
        return self._process_mal_to_anilist(mal_to_anilist)
        
    def get_airing_res(self, variables, page=1):
        query = '''
        query (
                $weekStart: Int,
                $weekEnd: Int,
                $page: Int,
        ){
                Page(page: $page) {
                        pageInfo {
                                hasNextPage
                                total
                        }
                        airingSchedules(
                                airingAt_greater: $weekStart
                                airingAt_lesser: $weekEnd
                        ) {
                                id
                                episode
                                airingAt
                                media {
                                        
        id
        idMal
        title {
                romaji
                userPreferred
                english
        }
        description
        genres
        averageScore
        isAdult
        rankings {
                rank
                type
                season
        }
        coverImage {
                extraLarge
        }
                                }
                        }
                }
        }
        '''

        result = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = result.json()

        if results.has_key("errors"):
            return

        json_res = results['data']['Page']
        return json_res

    def get_base_res(self, variables, page=1):
        query = '''
        query (
            $page: Int = 1,
            $type: MediaType,
            $isAdult: Boolean = false,
            $format:[MediaFormat],
            $season: MediaSeason,
            $year: String,
            $sort: [MediaSort] = [POPULARITY_DESC, SCORE_DESC]
        ) {
            Page (page: $page, perPage: 20) {
                pageInfo {
                    hasNextPage
                }
                ANIME: media (
                    format_in: $format,
                    type: $type,
                    season: $season,
                    startDate_like: $year,
                    sort: $sort,
                    isAdult: $isAdult
                ) {
                    id
                    idMal
                    title {
                        userPreferred,
                        romaji,
                        english
                    }
                    coverImage {
                        extraLarge
                    }
                    startDate {
                        year,
                        month,
                        day
                    }
                    description
                    synonyms
                    format
                    episodes
                    status
                    genres
                    duration
                }
            }
        }
        '''

        result = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = result.json()

        if results.has_key("errors"):
            return

        json_res = results['data']['Page']
        return json_res

    def get_search_res(self, variables, page=1):
        query = '''
        query (
            $page: Int = 1,
            $type: MediaType,
            $isAdult: Boolean = false,
            $search: String,
            $sort: [MediaSort] = [SCORE_DESC, POPULARITY_DESC]
        ) {
            Page (page: $page, perPage: 20) {
                pageInfo {
                    hasNextPage
                }
                ANIME: media (
                    type: $type,
                    search: $search,
                    sort: $sort,
                    isAdult: $isAdult
                ) {
                    id
                    idMal
                    title {
                        userPreferred,
                        romaji,
                        english
                    }
                    coverImage {
                        extraLarge
                    }
                    startDate {
                        year,
                        month,
                        day
                    }
                    description
                    synonyms
                    format
                    episodes
                    status
                    genres
                    duration
                }
            }
        }
        '''

        result = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = result.json()

        if results.has_key("errors"):
            return

        json_res = results['data']['Page']
        return json_res

    def get_recommendations_res(self, variables, page=1):
        query = '''
        query media($id:Int,$page:Int){Media(id:$id) {
            id
            recommendations (page:$page, perPage: 20, sort:[RATING_DESC,ID]) {
                pageInfo {
                    hasNextPage
                }
                nodes {
                    mediaRecommendation {
                        id
                        idMal
                        title {
                            userPreferred,
                            romaji,
                            english
                        }
                        format
                        type
                        status
                        coverImage {
                            extraLarge
                        }
                        startDate {
                            year,
                            month,
                            day
                        }
                        description
                        duration
                        genres
                        synonyms
                        episodes
                    }
                }
            }
        }
                                       }
        '''

        result = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = result.json()

        if results.has_key("errors"):
            return

        json_res = results['data']['Media']['recommendations']
        return json_res

    def get_anilist_res(self, variables):
        query = '''
        query($id: Int, $type: MediaType){Media(id: $id, type: $type) {
            id
            idMal
            title {
                userPreferred,
                romaji,
                english
            }
            coverImage {
                extraLarge
            }
            startDate {
                year,
                month,
                day
            }
            description
            synonyms
            format
            episodes
            status
            genres
            duration
            }
        }
        '''

        result = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = result.json()

        if results.has_key("errors"):
            return

        json_res = results['data']['Media']
        return json_res 

    def get_mal_to_anilist_res(self, variables):
        query = '''
        query($id: Int, $type: MediaType){Media(idMal: $id, type: $type) {
            id
            idMal
            title {
                userPreferred,
                romaji,
                english
            }
            coverImage {
                extraLarge
            }
            startDate {
                year,
                month,
                day
            }
            description
            synonyms
            format
            episodes
            status
            genres
            duration
            }
        }
        '''

        result = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = result.json()

        if results.has_key("errors"):
            return

        json_res = results['data']['Media'] 
        return json_res  

    def _process_anilist_view(self, json_res, base_plugin_url, page):
        hasNextPage = json_res['pageInfo']['hasNextPage']

        all_results = map(self._base_anilist_view, json_res['ANIME'])
        all_results = list(itertools.chain(*all_results))

        all_results += self._handle_paging(hasNextPage, base_plugin_url, page)
        return all_results

    def _process_airing_view(self, json_res):
        filter_json = filter(lambda x: x['media']['isAdult'] == False, json_res['airingSchedules'])
        ts = int(time.time())
        mapfunc = partial(self._base_airing_view, ts=ts)
        all_results = map(mapfunc, filter_json)
        return all_results

    def _process_recommendation_view(self, json_res, base_plugin_url, page):
        hasNextPage = json_res['pageInfo']['hasNextPage']
        res = [i['mediaRecommendation'] for i in json_res['nodes']]
        all_results = map(self._base_anilist_view, res)
        all_results = list(itertools.chain(*all_results))

        all_results += self._handle_paging(hasNextPage, base_plugin_url, page)
        return all_results

    def _process_mal_to_anilist(self, res):
        titles = self._get_titles(res)
        start_date = self._get_start_date(res)
        database._update_show(
            res['id'],
            res.get('idMal'),
            str({'name': res['title']['userPreferred'], 'start_date': start_date, 'episodes': res['episodes'], 'query': titles, 'poster':res['coverImage']['extraLarge']})
            )

        return  database.get_show(str(res['id']))

    def _base_anilist_view(self, res):
        in_database = database.get_show(str(res['id']))

        if not in_database:
            titles = self._get_titles(res)
            start_date = self._get_start_date(res)
            database._update_show(
                res['id'],
                res.get('idMal'),
                str({'name': res['title']['userPreferred'], 'start_date': start_date, 'episodes': res['episodes'], 'query': titles, 'poster':res['coverImage']['extraLarge']})
                )

        #remove cached eps for releasing shows every five days so new eps metadata can be shown
        if res.get('status') == 'RELEASING':
            try:
                from datetime import datetime, timedelta
                check_update = (datetime.today() - timedelta(days=5)).strftime('%Y-%m-%d')
                last_updated = database.get_episode_list(res['id'])[0]['last_updated']
                if check_update == last_updated:
                    database.remove_episodes(res['id'])
            except:
                pass

        kodi_meta = ast.literal_eval(database.get_show(str(res['id']))['kodi_meta'])

        title = res['title'][self._TITLE_LANG]
        if not title:
            title = res['title']['userPreferred']

        info = {}

        try:
            info['genre'] = res.get('genres')
        except:
            pass

        try:
            info['plot'] = res['description']
        except:
            pass

        try:
            info['title'] = title
        except:
            pass

        try:
            info['duration'] = res.get('duration') * 60
        except:
            pass

        try:
            start_date = res.get('startDate')
            info['aired'] = '{}-{:02}-{:02}'.format(start_date['year'], start_date['month'], start_date['day'])
        except:
            pass

        try:
            info['status'] = res.get('status')
        except:
            pass

        info['mediatype'] = 'tvshow'

        base = {
            "name": title,
            "url": "animes/%s/%s" % (res['id'], res.get('idMal')),
            "image": res['coverImage']['extraLarge'],
            "fanart": kodi_meta.get('fanart', res['coverImage']['extraLarge']),
            "info": info
        }

        if res['format'] == 'MOVIE' and res['episodes'] == 1:
            base['url'] = "play_movie/%s/1" % (res['id'])
            base['info']['mediatype'] = 'movie'
            return self._parse_view(base, False)

        return self._parse_view(base)

    def _base_airing_view(self, res, ts):
        airingAt = datetime.datetime.fromtimestamp(res['airingAt'])
        airingAt_day = airingAt.strftime('%A')
        airingAt_time = airingAt.strftime('%I:%M %p')
        airing_status = 'airing' if res['airingAt'] > ts else 'aired'
        rank = None
        rankings = res['media']['rankings']
        if rankings and rankings[-1]['season']:
            rank = rankings[-1]['rank']
        genres = res['media']['genres']
        if genres:
            genres = ' | '.join(genres[:3])
        title = res['media']['title'][self._TITLE_LANG]
        if not title:
            title = res['media']['title']['userPreferred']

        base = {
            'release_title': title,
            'poster': res['media']['coverImage']['extraLarge'],
            'ep_title': '{} {} {}'.format(res['episode'], airing_status, airingAt_day),
            'ep_airingAt': airingAt_time,
            'averageScore': res['media']['averageScore'],
            'rank': rank,
            'plot': res['media']['description'],
            'genres': genres,
            'id': res['media']['id']
            }
            
        return base

    def _get_titles(self, res):
        titles = list(set(res['title'].values()))
        if res['format'] == 'MOVIE':
            titles = res['title'].values()
        titles = filter(lambda x: all(ord(char) < 128 for char in x) if x else [], titles)[:3]
        query_titles = '({})'.format(')|('.join(map(str, titles)))
        return query_titles

    def _get_start_date(self, res):
        try:
            start_date = res.get('startDate')
            start_date = '{}-{:02}-{:02}'.format(start_date['year'], start_date['month'], start_date['day'])
        except:
            start_date = 'null'

        return start_date

    def _parse_view(self, base, is_dir=True):
        return [
            utils.allocate_item("%s" % base["name"],
                                base["url"],
                                is_dir,
                                base["image"],
                                base["info"],
                                base["fanart"],
                                base["image"])
            ]

    def get_genres(self, genre_dialog):
        query = '''
        query {
            genres: GenreCollection,
            tags: MediaTagCollection {
                name
                isAdult
            }
        }
        '''

        result = requests.post(self._URL, json={'query': query})
        results = result.json()['data']
        genres_list = results['genres']

        del genres_list[6]

        tags_list = []
        tags = filter(lambda x: x['isAdult'] == False, results['tags'])
        for tag in tags:
            tags_list.append(tag['name'])

        genre_display_list = genres_list + tags_list
        return self._select_genres(genre_dialog, genre_display_list)

    def _select_genres(self, genre_dialog, genre_display_list):
        multiselect = genre_dialog(genre_display_list)

        if not multiselect:
            return []

        genre_list = []
        tag_list = []

        for selection in multiselect:
            if selection <= 17:
                genre_list.append(genre_display_list[selection])
                continue

            tag_list.append(genre_display_list[selection])

        return self._genres_payload(genre_list, tag_list)

    def _genres_payload (self, genre_list, tag_list, page=1):
        query = '''
        query (
            $page: Int,
            $type: MediaType,
            $isAdult: Boolean = false,
            $includedGenres: [String],
            $includedTags: [String],
            $sort: [MediaSort] = [SCORE_DESC, POPULARITY_DESC]
        ) {
            Page (page: $page, perPage: 20) {
                pageInfo {
                    hasNextPage
                }
                ANIME: media (
                    type: $type,
                    genre_in: $includedGenres,
                    tag_in: $includedTags,
                    sort: $sort,
                    isAdult: $isAdult
                ) {
                    id
                    title {
                        userPreferred,
                        romaji,
                        english
                    }
                    coverImage {
                        extraLarge
                    }
                    startDate {
                        year,
                        month,
                        day
                    }
                    description
                    synonyms
                    format
                    episodes
                    status
                    genres
                    duration
                    isAdult
                    }
                }
            }
        '''

        variables = {
            'page': page,
            'type': "ANIME"
            }

        if genre_list:
            variables["includedGenres"] = genre_list

        if tag_list:
            variables["includedTags"] = tag_list

        return self._process_genre_view(query, variables, "anilist_genres/%s/%s/%%d" %(genre_list, tag_list), page)

    def _process_genre_view(self, query, variables, base_plugin_url, page):
        result = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = result.json()

        if results.has_key("errors"):
            return

        anime_res = results['data']['Page']['ANIME']
        hasNextPage = results['data']['Page']['pageInfo']['hasNextPage']

        all_results = map(self._base_anilist_view, anime_res)
        all_results = list(itertools.chain(*all_results))

        all_results += self._handle_paging(hasNextPage, base_plugin_url, page)
        return all_results

    def get_genres_page(self, genre_string, tag_string, page):
        return self._genres_payload(ast.literal_eval(genre_string), ast.literal_eval(tag_string), page)
