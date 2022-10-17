import itertools
import time
import datetime
import ast
import json
import random
from functools import partial
from resources.lib.ui import utils, database, client, get_meta, control
from resources.lib.ui.divide_flavors import div_flavor
import pickle
import six


class AniListBrowser():
    _URL = "https://graphql.anilist.co"

    def __init__(self, title_key=None):
        if title_key:
            self._TITLE_LANG = self._title_lang(title_key)
        else:
            self._TITLE_LANG = "userPreferred"
        self.format_in_type = ''
        filterEnable = control.getSetting('contentformat.bool') == "true"
        if filterEnable:
            self.format_in_type = control.getSetting('contentformat.menu')

    def _title_lang(self, title_key):
        title_lang = {
            "40370": "userPreferred",
            "Romaji (Shingeki no Kyojin)": "userPreferred",
            "40371": "english",
            "English (Attack on Titan)": "english"
        }

        return title_lang[title_key]

    def _handle_paging(self, hasNextPage, base_url, page):
        if not hasNextPage:
            return []

        next_page = page + 1
        name = "Next Page (%d)" % (next_page)
        return [utils.allocate_item(name, base_url % next_page, True, 'next.png', fanart='next.png')]

    def get_season_year(self, period='current'):
        date = datetime.datetime.today()
        year = date.year
        month = date.month
        seasons = ['WINTER', 'SPRING', 'SUMMER', 'FALL']
        if period == "next":
            season = seasons[int((month - 1) / 3 + 1) % 4]
            if season == 'WINTER':
                year += 1
        else:
            season = seasons[int((month - 1) / 3)]
        return [season, year]

    def get_airing_anime(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'status': "RELEASING",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        airing_anime = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(airing_anime, "anilist_airing_anime/%d", page)

    def get_trending_this_year(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'year': str(year) + '%',
            'sort': "TRENDING_DESC",
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        trending = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(trending, "anilist_trending_this_year/%d", page)

    def get_popular_this_year(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC",
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        popular = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(popular, "anilist_popular_this_year/%d", page)

    def get_voted_this_year(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'year': str(year) + '%',
            'sort': "FAVOURITES_DESC",
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        voted = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(voted, "anilist_voted_this_year/%d", page)

    def get_upcoming_next_year(self, page=1, format_in=''):
        season, year = self.get_season_year('next')
        variables = {
            'page': page,
            'type': "ANIME",
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        upcoming = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(upcoming, "anilist_upcoming_next_year/%d", page)

    def get_trending_this_season(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "TRENDING_DESC",
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        trending = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(trending, "anilist_trending_this_season/%d", page)

    def get_popular_this_season(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC",
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        popular = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(popular, "anilist_popular_this_season/%d", page)

    def get_voted_this_season(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "FAVOURITES_DESC",
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        voted = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(voted, "anilist_voted_this_season/%d", page)

    def get_upcoming_next_season(self, page=1, format_in=''):
        season, year = self.get_season_year('next')
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        upcoming = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(upcoming, "anilist_upcoming_next_season/%d", page)

    def get_all_time_trending(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "TRENDING_DESC"
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        all_time_trending = database.get(self.get_base_res, 24, variables, page)
        return self._process_anilist_view(all_time_trending, "anilist_all_time_trending/%d", page)

    def get_all_time_popular(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        all_time_popular = database.get(self.get_base_res, 24, variables, page)
        return self._process_anilist_view(all_time_popular, "anilist_all_time_popular/%d", page)

    def get_all_time_voted(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "FAVOURITES_DESC"
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        all_time_voted = database.get(self.get_base_res, 24, variables, page)
        return self._process_anilist_view(all_time_voted, "anilist_all_time_voted/%d", page)

    def get_top_100_anime(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "SCORE_DESC"
        }

        if self.format_in_type:
            variables['format'] = [self.format_in_type.upper()]

        top_100_anime = database.get(self.get_base_res, 24, variables, page)
        return self._process_anilist_view(top_100_anime, "anilist_top_100_anime/%d", page)

    def get_airing_anime_movie(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'status': "RELEASING",
            'sort': "POPULARITY_DESC",
            'format': "MOVIE"
        }

        airing_anime = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(airing_anime, "anilist_airing_anime_movie/%d", page)

    def get_trending_this_year_movie(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'year': str(year) + '%',
            'sort': "TRENDING_DESC",
            'format': "MOVIE"
        }

        trending = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(trending, "anilist_trending_this_year_movie/%d", page)

    def get_popular_this_year_movie(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC",
            'format': "MOVIE"
        }

        popular = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(popular, "anilist_popular_this_year_movie/%d", page)

    def get_voted_this_year_movie(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'year': str(year) + '%',
            'sort': "FAVOURITES_DESC",
            'format': "MOVIE"
        }

        voted = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(voted, "anilist_voted_this_year_movie/%d", page)

    def get_upcoming_next_year_movie(self, page=1, format_in=''):
        season, year = self.get_season_year('next')
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC",
            'format': "MOVIE"
        }

        upcoming = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(upcoming, "anilist_upcoming_next_year_movie/%d", page)

    def get_trending_this_season_movie(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "TRENDING_DESC",
            'format': "MOVIE"
        }

        trending = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(trending, "anilist_trending_this_season_movie/%d", page)

    def get_popular_this_season_movie(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC",
            'format': "MOVIE"
        }

        popular = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(popular, "anilist_popular_this_season_movie/%d", page)

    def get_voted_this_season_movie(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "FAVOURITES_DESC",
            'format': "MOVIE"
        }

        voted = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(voted, "anilist_voted_this_season_movie/%d", page)

    def get_upcoming_next_season_movie(self, page=1, format_in=''):
        season, year = self.get_season_year('next')
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC",
            'format': "MOVIE"
        }

        upcoming = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(upcoming, "anilist_upcoming_next_season_movie/%d", page)

    def get_all_time_trending_movie(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "TRENDING_DESC",
            'format': "MOVIE"
        }

        all_time_trending = database.get(self.get_base_res, 24, variables, page)
        return self._process_anilist_view(all_time_trending, "anilist_all_time_trending_movie/%d", page)

    def get_all_time_popular_movie(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "POPULARITY_DESC",
            'format': "MOVIE"
        }

        all_time_popular = database.get(self.get_base_res, 24, variables, page)
        return self._process_anilist_view(all_time_popular, "anilist_all_time_popular_movie/%d", page)

    def get_all_time_voted_movie(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "FAVOURITES_DESC",
            'format': "MOVIE"
        }

        all_time_voted = database.get(self.get_base_res, 24, variables, page)
        return self._process_anilist_view(all_time_voted, "anilist_all_time_voted_movie/%d", page)

    def get_top_100_anime_movie(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "SCORE_DESC",
            'format': "MOVIE"
        }

        top_100_anime = database.get(self.get_base_res, 24, variables, page)
        return self._process_anilist_view(top_100_anime, "anilist_top_100_anime_movie/%d", page)

    def get_airing_anime_tv(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'status': "RELEASING",
            'sort': "POPULARITY_DESC",
            'format': "TV"
        }

        airing_anime = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(airing_anime, "anilist_airing_anime_tv/%d", page)

    def get_trending_this_year_tv(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'year': str(year) + '%',
            'sort': "TRENDING_DESC",
            'format': "TV"
        }

        trending = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(trending, "anilist_trending_this_year_tv/%d", page)

    def get_popular_this_year_tv(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC",
            'format': "TV"
        }

        popular = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(popular, "anilist_popular_this_year_tv/%d", page)

    def get_voted_this_year_tv(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'year': str(year) + '%',
            'sort': "FAVOURITES_DESC",
            'format': "TV"
        }

        voted = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(voted, "anilist_voted_this_year_tv/%d", page)

    def get_upcoming_next_year_tv(self, page=1, format_in=''):
        season, year = self.get_season_year('next')
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC",
            'format': "TV"
        }

        upcoming = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(upcoming, "anilist_upcoming_next_year_tv/%d", page)

    def get_trending_this_season_tv(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "TRENDING_DESC",
            'format': "TV"
        }

        trending = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(trending, "anilist_trending_this_season_tv/%d", page)

    def get_popular_this_season_tv(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC",
            'format': "TV"
        }

        popular = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(popular, "anilist_popular_this_season_tv/%d", page)

    def get_voted_this_season_tv(self, page=1, format_in=''):
        season, year = self.get_season_year()
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "FAVOURITES_DESC",
            'format': "TV"
        }

        voted = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(voted, "anilist_voted_this_season_tv/%d", page)

    def get_upcoming_next_season_tv(self, page=1, format_in=''):
        season, year = self.get_season_year('next')
        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC",
            'format': "TV"
        }

        upcoming = database.get(self.get_base_res, 0.125, variables, page)
        return self._process_anilist_view(upcoming, "anilist_upcoming_next_season_tv/%d", page)

    def get_all_time_trending_tv(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "TRENDING_DESC",
            'format': "TV"
        }

        all_time_trending = database.get(self.get_base_res, 24, variables, page)
        return self._process_anilist_view(all_time_trending, "anilist_all_time_trending_tv/%d", page)

    def get_all_time_popular_tv(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "POPULARITY_DESC",
            'format': "TV"
        }

        all_time_popular = database.get(self.get_base_res, 24, variables, page)
        return self._process_anilist_view(all_time_popular, "anilist_all_time_popular_tv/%d", page)

    def get_all_time_voted_tv(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "FAVOURITES_DESC",
            'format': "TV"
        }

        all_time_voted = database.get(self.get_base_res, 24, variables, page)
        return self._process_anilist_view(all_time_voted, "anilist_all_time_voted_tv/%d", page)

    def get_top_100_anime_tv(self, page=1, format_in=''):
        variables = {
            'page': page,
            'type': "ANIME",
            'sort': "SCORE_DESC",
            'format': "TV"
        }

        top_100_anime = database.get(self.get_base_res, 24, variables, page)
        return self._process_anilist_view(top_100_anime, "anilist_top_100_anime_tv/%d", page)

    def get_airing(self, page=1, format_in=''):
        airing = database.get(self._get_airing, 12, page, self.format_in_type)
        return airing

    def _get_airing(self, page=1, format_in=''):
        today = datetime.date.today()
        today_ts = int(time.mktime(today.timetuple()))
        weekStart = today_ts - 86400
        weekEnd = today_ts + (86400 * 6)

        variables = {
            'weekStart': weekStart,
            'weekEnd': weekEnd,
            'page': page
        }

        list_ = []

        for i in range(0, 4):
            popular = self.get_airing_res(variables, page)
            list_.append(popular)

            if not popular['pageInfo']['hasNextPage']:
                break

            page += 1
            variables['page'] = page

        results = list(map(self._process_airing_view, list_))
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
                        bannerImage
                    }
                }
            }
        }
        '''

        result = client.request(self._URL, post={'query': query, 'variables': variables}, jpost=True)
        results = json.loads(result)

        if "errors" in results.keys():
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
            $status: MediaStatus,
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
                    status: $status
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
                    bannerImage
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
                    countryOfOrigin
                    averageScore
                    characters (
                        page: 1,
                        sort: ROLE,
                        perPage: 10,
                    ) {
                        edges {
                            node {
                                name {
                                    userPreferred
                                }
                            }
                            voiceActors (language: JAPANESE) {
                                name {
                                    userPreferred
                                }
                                image {
                                    large
                                }
                            }
                        }
                    }
                    studios {
                        edges {
                            node {
                                name
                            }
                        }
                    }
                    trailer {
                        id
                        site
                    }
                }
            }
        }
        '''

        result = client.request(self._URL, post={'query': query, 'variables': variables}, jpost=True)
        results = json.loads(result)

        if "errors" in results.keys():
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
                    bannerImage
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
                    countryOfOrigin
                    averageScore
                    characters (
                        page: 1,
                        sort: ROLE,
                        perPage: 10,
                    ) {
                        edges {
                            node {
                                name {
                                    userPreferred
                                }
                            }
                            voiceActors (language: JAPANESE) {
                                name {
                                    userPreferred
                                }
                                image {
                                    large
                                }
                            }
                        }
                    }
                    studios {
                        edges {
                            node {
                                name
                            }
                        }
                    }
                    trailer {
                        id
                        site
                    }
                }
            }
        }
        '''

        result = client.request(self._URL, post={'query': query, 'variables': variables}, jpost=True)
        results = json.loads(result)

        if "errors" in results.keys():
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
                        bannerImage
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
                        countryOfOrigin
                        averageScore
                        characters (
                            page: 1,
                            sort: ROLE,
                            perPage: 10,
                        ) {
                            edges {
                                node {
                                    name {
                                        userPreferred
                                    }
                                }
                                voiceActors (language: JAPANESE) {
                                    name {
                                        userPreferred
                                    }
                                    image {
                                        large
                                    }
                                }
                            }
                        }
                        studios {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                        trailer {
                            id
                            site
                        }
                    }
                }
            }
        }
                                       }
        '''

        result = client.request(self._URL, post={'query': query, 'variables': variables}, jpost=True)
        results = json.loads(result)

        if "errors" in results.keys():
            return

        json_res = results['data']['Media']['recommendations']
        return json_res

    def get_anilist_res(self, variables):
        query = '''
        query($id: Int, $type: MediaType){
            Media(id: $id, type: $type) {
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
                bannerImage
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
                countryOfOrigin
                averageScore
                characters (
                    page: 1,
                    sort: ROLE,
                    perPage: 10,
                ) {
                    edges {
                        node {
                            name {
                                userPreferred
                            }
                        }
                        voiceActors (language: JAPANESE) {
                            name {
                                userPreferred
                            }
                            image {
                                large
                            }
                        }
                    }
                }
                studios {
                    edges {
                        node {
                            name
                        }
                    }
                }
                trailer {
                    id
                    site
                }
            }
        }
        '''

        result = client.request(self._URL, post={'query': query, 'variables': variables}, jpost=True)
        results = json.loads(result)

        if "errors" in results.keys():
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
            bannerImage
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
            countryOfOrigin
            averageScore
            characters (
                page: 1,
                sort: ROLE,
                perPage: 10,
            ) {
                edges {
                    node {
                        name {
                            userPreferred
                        }
                    }
                    voiceActors (language: JAPANESE) {
                        name {
                            userPreferred
                        }
                        image {
                            large
                        }
                    }
                }
            }
            studios {
                edges {
                    node {
                        name
                    }
                }
            }
            trailer {
                id
                site
            }
            }
        }
        '''

        result = client.request(self._URL, post={'query': query, 'variables': variables}, jpost=True)
        results = json.loads(result)

        if "errors" in results.keys():
            return

        json_res = results['data']['Media']
        return json_res

    @div_flavor
    def _process_anilist_view(self, json_res, base_plugin_url, page, dub=False):
        hasNextPage = json_res['pageInfo']['hasNextPage']

        if dub:
            mapfunc = partial(self._base_anilist_view, mal_dub=dub)
        else:
            mapfunc = self._base_anilist_view

        _ = get_meta.collect_meta(json_res['ANIME'])
        all_results = map(mapfunc, json_res['ANIME'])
        all_results = list(itertools.chain(*all_results))

        all_results += self._handle_paging(hasNextPage, base_plugin_url, page)
        return all_results

    def _process_airing_view(self, json_res):
        # filter_json = filter(lambda x: x['media']['isAdult'] == False, json_res['airingSchedules'])
        filter_json = [x for x in json_res['airingSchedules'] if x['media']['isAdult'] is False]
        ts = int(time.time())
        mapfunc = partial(self._base_airing_view, ts=ts)
        all_results = list(map(mapfunc, filter_json))
        return all_results

    @div_flavor
    def _process_recommendation_view(self, json_res, base_plugin_url, page, dub=False):
        hasNextPage = json_res['pageInfo']['hasNextPage']
        res = [i['mediaRecommendation'] for i in json_res['nodes']]

        if dub:
            mapfunc = partial(self._base_anilist_view, mal_dub=dub)
        else:
            mapfunc = self._base_anilist_view

        all_results = list(map(mapfunc, res))
        all_results = list(itertools.chain(*all_results))

        all_results += self._handle_paging(hasNextPage, base_plugin_url, page)
        return all_results

    def _process_mal_to_anilist(self, res):
        # titles = self._get_titles(res)
        # start_date = self._get_start_date(res)
        self._database_update_show(res)
        _ = get_meta.collect_meta([res])

        return database.get_show(str(res['id']))

    def _base_anilist_view(self, res, mal_dub=None):
        in_database = database.get_show(res['id'])

        if not in_database:
            self._database_update_show(res)

        # remove cached eps for releasing shows every five days so new eps metadata can be shown
        if res.get('status') == 'RELEASING':
            from datetime import date
            ep_list = database.get_episode_list(res['id'])
            if ep_list:
                last_updated = ep_list[0]['last_updated']
                if six.PY2:
                    year, month, day = last_updated.split('-')
                    ldate = date(int(year), int(month), int(day))
                else:
                    ldate = date.fromisoformat(last_updated)
                ldiff = date.today() - ldate
                if ldiff.days > 4:
                    database.remove_episodes(res['id'])

        kodi_meta = {}
        show_meta = database.get_show_meta(res['id'])
        if show_meta:
            kodi_meta.update(pickle.loads(show_meta.get('art')))

        title = res.get('title').get(self._TITLE_LANG)
        if not title:
            title = res.get('title').get('userPreferred')

        info = {}

        info['genre'] = res.get('genres')

        desc = res.get('description')
        if desc:
            desc = desc.replace('<i>', '[I]').replace('</i>', '[/I]')
            desc = desc.replace('<b>', '[B]').replace('</b>', '[/B]')
            desc = desc.replace('<br>', '[CR]')
            desc = desc.replace('\n', '')
            info['plot'] = desc

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
            info['premiered'] = '{}-{:02}-{:02}'.format(start_date['year'], start_date['month'], start_date['day'])
            info['year'] = start_date['year']
        except:
            pass

        try:
            info['status'] = res.get('status')
        except:
            pass

        info['mediatype'] = 'tvshow'

        info['country'] = res.get('countryOfOrigin', '')

        try:
            cast = []
            cast2 = []
            for x in res.get('characters').get('edges'):
                role = x.get('node').get('name').get('userPreferred')
                actor = x.get('voiceActors')[0].get('name').get('userPreferred')
                actor_hs = x.get('voiceActors')[0].get('image').get('large')
                cast.append((actor, role))
                cast2.append({'name': actor, 'role': role, 'thumbnail': actor_hs})
            info['cast'] = cast
            info['cast2'] = cast2
        except:
            pass

        try:
            info['studio'] = [x.get('node').get('name') for x in res.get('studios').get('edges')]
        except:
            pass

        try:
            info['rating'] = res.get('averageScore') / 10.0
        except:
            pass

        try:
            if res.get('trailer').get('site') == 'youtube':
                info['trailer'] = 'plugin://plugin.video.youtube/play/?video_id={0}'.format(res.get('trailer').get('id'))
            else:
                info['trailer'] = 'plugin://plugin.video.dailymotion_com/?url={0}&mode=playVideo'.format(res.get('trailer').get('id'))
        except:
            pass

        dub = False
        mal_id = str(res.get('idMal', 0))
        if mal_dub and mal_dub.get(mal_id):
            dub = True

        base = {
            "name": title,
            "url": "animes/%s/%s/" % (res['id'], res.get('idMal')),
            "image": res['coverImage']['extraLarge'],
            "poster": res['coverImage']['extraLarge'],
            "fanart": res['coverImage']['extraLarge'],
            "banner": res.get('bannerImage'),
            "info": info,
        }

        if kodi_meta.get('fanart'):
            base['fanart'] = random.choice(kodi_meta.get('fanart'))
        if kodi_meta.get('thumb'):
            base['landscape'] = random.choice(kodi_meta.get('thumb'))
        if kodi_meta.get('clearart'):
            base['clearart'] = random.choice(kodi_meta.get('clearart'))
        if kodi_meta.get('clearlogo'):
            base['clearlogo'] = random.choice(kodi_meta.get('clearlogo'))

        if res['format'] in ['MOVIE', 'ONA'] and res['episodes'] == 1:
            base['url'] = "play_movie/%s/1/" % (res['id'])
            base['info']['mediatype'] = 'movie'
            return self._parse_view(base, False, dub=dub)

        return self._parse_view(base, dub=dub)

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

    def _database_update_show(self, res):
        titles = self._get_titles(res)
        start_date = self._get_start_date(res)
        title_userPreferred = res['title'][self._TITLE_LANG]
        if not title_userPreferred:
            title_userPreferred = res['title']['userPreferred']

        kodi_meta = {}
        name = res['title']['romaji']
        name = name.encode('utf-8') if six.PY2 else name
        kodi_meta['name'] = name
        ename = res['title']['english']
        if ename:
            ename = ename.encode('utf-8') if six.PY2 else ename
        kodi_meta['ename'] = ename
        kodi_meta['title_userPreferred'] = title_userPreferred.encode('utf-8') if six.PY2 else title_userPreferred
        kodi_meta['start_date'] = start_date
        kodi_meta['query'] = titles
        kodi_meta['episodes'] = res['episodes']
        kodi_meta['poster'] = res['coverImage']['extraLarge']
        kodi_meta['status'] = res.get('status')
        kodi_meta['format'] = res.get('format')
        if res.get('format') != 'TV':
            if res.get('averageScore'):
                kodi_meta['rating'] = res.get('averageScore') / 10.0
            desc = res.get('description')
            if desc:
                desc = desc.replace('<i>', '[I]').replace('</i>', '[/I]')
                desc = desc.replace('<b>', '[B]').replace('</b>', '[/B]')
                desc = desc.replace('<br>', '[CR]')
                desc = desc.replace('\n', '')
                kodi_meta['plot'] = desc.encode('utf-8') if six.PY2 else desc

        database._update_show(
            res['id'],
            res.get('idMal'),
            pickle.dumps(kodi_meta)
        )

    def _get_titles(self, res):
        # titles = list(set(res['title'].values()))
        # if res['format'] == 'MOVIE':
        #     titles = list(res['title'].values())
        # # titles = [x for x in titles if (all(ord(char) < 128 for char in x) if x else [])][:3]
        # titles = [x.encode('utf-8') if six.PY2 else x for x in titles if x][:3]
        # query_titles = '({})'.format(')|('.join(map(str, titles)))
        name = res['title']['romaji']
        name = name.encode('utf-8') if six.PY2 else name
        ename = res['title']['english']
        if ename:
            ename = ename.encode('utf-8') if six.PY2 else ename
        query_titles = '({0})|({1})'.format(name, ename)
        return query_titles

    def _get_start_date(self, res):
        try:
            start_date = res.get('startDate')
            start_date = '{}-{:02}-{:02}'.format(start_date['year'], start_date['month'], start_date['day'])
        except:
            start_date = 'null'

        return start_date

    def _parse_view(self, base, is_dir=True, dub=False):
        if dub:
            return self._parse_div_view(base, is_dir)
        return [
            utils.allocate_item(
                base["name"],
                base["url"],
                is_dir=is_dir,
                image=base["image"],
                info=base["info"],
                fanart=base["fanart"],
                poster=base["image"],
                landscape=base.get("landscape"),
                banner=base.get("banner"),
                clearart=base.get("clearart"),
                clearlogo=base.get("clearlogo")
            )
        ]

    def _parse_div_view(self, base, is_dir):
        parsed_view = [
            utils.allocate_item(
                "%s" % base["name"],
                base["url"] + '2',
                is_dir,
                image=base["image"],
                info=base["info"],
                fanart=base["fanart"],
                poster=base["image"],
                landscape=base.get("landscape"),
                banner=base.get("banner"),
                clearart=base.get("clearart"),
                clearlogo=base.get("clearlogo")
            )
        ]

        parsed_view.append(
            utils.allocate_item(
                "%s (Dub)" % base["name"],
                base["url"] + '0',
                is_dir,
                image=base["image"],
                info=base["info"],
                fanart=base["fanart"],
                poster=base["image"],
                landscape=base.get("landscape"),
                banner=base.get("banner"),
                clearart=base.get("clearart"),
                clearlogo=base.get("clearlogo")
            )
        )

        return parsed_view

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

        result = client.request(self._URL, post={'query': query}, jpost=True)
        results = json.loads(result)['data']
        genres_list = results['genres']

        del genres_list[6]

        tags_list = []
        # tags = filter(lambda x: x['isAdult'] == False, results['tags'])
        tags = [x for x in results['tags'] if x['isAdult'] is False]
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

    def _genres_payload(self, genre_list, tag_list, page=1):
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
                    idMal
                    title {
                        userPreferred,
                        romaji,
                        english
                    }
                    coverImage {
                        extraLarge
                    }
                    bannerImage
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
                    countryOfOrigin
                    averageScore
                    characters (
                        page: 1,
                        sort: ROLE,
                        perPage: 10,
                    ) {
                        edges {
                            node {
                                name {
                                    userPreferred
                                }
                            }
                            voiceActors (language: JAPANESE) {
                                name {
                                    userPreferred
                                }
                                image {
                                    large
                                }
                            }
                        }
                    }
                    studios {
                        edges {
                            node {
                                name
                            }
                        }
                    }
                    trailer {
                        id
                        site
                    }
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

        return self._process_genre_view(query, variables, "anilist_genres/%s/%s/%%d" % (genre_list, tag_list), page)

    @div_flavor
    def _process_genre_view(self, query, variables, base_plugin_url, page, dub=False):
        result = client.request(self._URL, post={'query': query, 'variables': variables}, jpost=True)
        results = json.loads(result)

        if "errors" in results.keys():
            return

        anime_res = results['data']['Page']['ANIME']
        hasNextPage = results['data']['Page']['pageInfo']['hasNextPage']

        if dub:
            mapfunc = partial(self._base_anilist_view, mal_dub=dub)
        else:
            mapfunc = self._base_anilist_view

        _ = get_meta.collect_meta(anime_res)
        all_results = list(map(mapfunc, anime_res))
        all_results = list(itertools.chain(*all_results))

        all_results += self._handle_paging(hasNextPage, base_plugin_url, page)
        return all_results

    def get_genres_page(self, genre_string, tag_string, page):
        return self._genres_payload(ast.literal_eval(genre_string), ast.literal_eval(tag_string), page)
