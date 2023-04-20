import vk_api
from vk_api.exceptions import ApiError


class BackBot:

    def __init__(self, token):
        self.ext_api = vk_api.VkApi(token=token)

    def user_info(self, user_id):
        try:
            info = self.ext_api.method('users.get',
                                       {'user_id': user_id,
                                        'fields': 'bdate,city,relation,sex'
                                        }
                                       )
        except ApiError:
            return
        return info

    def user_search(self, city_id, age_from, age_to, sex, status, offset=None):
        try:
            profiles = self.ext_api.method('users.search',
                                           {'city_id': city_id,
                                            'age_from': age_from,
                                            'age_to': age_to,
                                            'sex': sex,
                                            'status': status,
                                            'count': 10,
                                            'offset': offset
                                            }
                                           )
        except ApiError:
            return

        profiles = profiles['items']
        result = []
        for profile in profiles:
            if profile['is_closed'] == False:
                result.append({'name': profile['first_name'] + ' ' + profile['last_name'],
                               'id': profile['id']
                               }
                              )
        return result

    def get_best_photos(self, user_id):

        profile_photos = self.ext_api.method('photos.get',
                                     {'album_id': 'profile',
                                      'owner_id': user_id,
                                      'extended': 1
                                      }
                                     )

        try:
            photos = profile_photos['items']
        except KeyError:
            return

        every_photos = []
        every_likes = []
        result = []
        if profile_photos['count'] > 50:   # Ограничение ВКонтакта. Выдаёт не более 50 фотографий профиля.
            count_pr_ph = 50
        else:
            count_pr_ph = profile_photos['count']

        for n in range(count_pr_ph):
            photo = photos[n]
            likes = photo['likes']
            every_photos.append({'owner_id': photo['owner_id'],
                                 'id': photo['id'],
                                 'likes': likes['count']
                                 }
                                )
            every_likes.append(likes['count'])

        every_likes.sort(reverse=True)
        if count_pr_ph > 3:
            counter = 3
        else:
            counter = count_pr_ph

        for n in range(counter):
            best_photo_likes = every_likes[n]
            for one_photo in every_photos:
                if best_photo_likes == one_photo['likes']:
                    result.append({'owner_id': one_photo['owner_id'],
                                   'id': one_photo['id']
                                   }
                                  )
        return result

