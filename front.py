import vk_api
import datetime

from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import bottoken, mytoken
from back import BackBot
from database import create_database, add_profiles, add_best_profile, get_best_profiles


class FrontBot:

    def __init__(self, token):
        self.bot = vk_api.VkApi(token=token)

    def send_message(self, user_id, message=None, attachment=None):
        self.bot.method('messages.send',
                        {'user_id': user_id,
                         'message': message,
                         'random_id': get_random_id(),
                         'attachment': attachment
                         }
                        )

    def adding_year(self, year, user_id, first_name, longpoll):

        self.send_message(user_id, f'Привет, {first_name}!\n У тебя не указан возраст, поиск невозможен.\n'
                                   f'Введи свой год рождения в формате XXXX (например 1995)')
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                user_text = event.text
                try:
                    user_year = int(user_text)
                    if year - 100 < user_year < year - 10:
                        bdate = [1, 1, user_year]
                        break
                    else:
                        self.send_message(user_id, f'Надо ввести реальный год рождения в формате XXXX (например 1995)')
                except ValueError:
                    self.send_message(user_id, f'Надо ввести число в формате XXXX (например 1995)')
        return bdate

    def info_for_searching(self, user_id, longpoll):

        year = datetime.datetime.today().year
        user_info = backbot.user_info(user_id)
        user_info = user_info[0]
        first_name = user_info['first_name']

        if 'city' not in user_info:
            self.send_message(user_id, f'Привет, {first_name}! У тебя не указан город, извини, поиск невозможен.')
            return

        city = user_info['city']
        city_id = city['id']
        searching_sex = 3 - user_info['sex']

        if 'bdate' not in user_info:
            bdate = self.adding_year(year, user_id, first_name, longpoll)
        else:
            bdate = user_info['bdate'].split('.')
            if len(bdate) < 3:
                bdate = self.adding_year(year, user_id, first_name, longpoll)

        byear = int(bdate[2])
        age_from = year - byear - 10
        age_to = year - byear + 10

        return [first_name, city_id, searching_sex, age_from, age_to]

    def viewing_profile(self, checking_profiles, counter, event_user_id, offset):

        counter += 1
        add_key = 1
        profile = checking_profiles[counter]
        name = profile['name']
        profile_id = profile['id']
        result = backbot.get_best_photos(profile_id)

        if result:
            self.send_message(event_user_id, f'{name}\nhttps://vk.com/id{profile_id}')
            for n in range(len(result)):
                photo = result[n]
                owner_id = photo['owner_id']
                id = photo['id']
                media = f'photo{owner_id}_{id}'
                self.send_message(event_user_id, attachment=media)
            self.send_message(event_user_id, 'Что бы запомнить данную анкету набери команду Добавить (или Add, или а)\n'
                                             'Для просмотра следующей анкеты набери команду Дальше (или Next, или n)'
                              )

        else:
            self.send_message(event_user_id, f'В профиле {name} нет фотографий.\n'
                                             f'Можешь посмотреть анкету, перейдя по ссылке:\n'
                                             f'https://vk.com/id{profile_id}\n'
                                             f'Что бы запомнить данную анкету набери команду Добавить (или Add, или а)\n'
                                             f'Для просмотра следующей анкеты набери команду Дальше (или Next, или n)'
                              )

        if counter == len(checking_profiles) - 1:
            offset += 10
            counter = -1

        return counter, offset, add_key, name, profile_id

    def handler(self):

        longpoll = VkLongPoll(self.bot)
        greatings_list = ['привет', 'привет!', 'hi', 'hi!', 'здравствуйте', 'здравствуйте!']
        info_for_searching = 'None'
        counter_data = 0
        add_key = 0
        search_key = 0

        for event in longpoll.listen():

            if event.type == VkEventType.MESSAGE_NEW and event.to_me:

                if info_for_searching == 'None':
                    info_for_searching = self.info_for_searching(event.user_id, longpoll)

                if info_for_searching is None:
                    return

                if event.text.lower() in greatings_list:
                    self.send_message(event.user_id, f'Привет, {info_for_searching[0]}!\n С тобой разговаривает '
                                                     f'чат-бот. Введи команду.\n(Помощь (Help, H) - список команд).'
                                      )

                elif event.text.lower() == 'помощь' or event.text.lower() == 'help' or event.text.lower() == 'h':
                    self.send_message(event.user_id, 'Список команд:\nПравила (Rules, R) - правила поиска.\n'
                                                     'Поиск (Search, S) - запуск поиска подходящих анкет.\n'
                                                     'Далее (Next, N) - продолжение поиска.\n'
                                                     'Добавить (Add, A) - сохранить анкету в Лучшие.\n'
                                                     'Лучшие (Best, B) - выводит список сохранённых анкет.\n'
                                                     'Помощь (Help, H) - данный текст.'
                                      )

                elif event.text.lower() == 'правила' or event.text.lower() == 'rules' or event.text.lower() == 'r':
                    self.send_message(event.user_id, 'Я нахожу анкеты холостых пользователей противоположного'
                                                     ' пола из города, где ты живёшь, и возрастом плюс-минус 10 лет'
                                                     ' от твоего. После чего показываю адрес анкеты и три лучшие'
                                                     ' фотографии профиля. Понравившиеся анкеты можно запомнить для'
                                                     ' более позднего просмотра.'
                                      )

                elif event.text.lower() == 'поиск' or event.text.lower() == 'search' or event.text.lower() == 's' and search_key == 0:
                    offset = 0
                    counter = -1
                    search_key = 1
                    profiles = backbot.user_search(info_for_searching[1], info_for_searching[3],
                                                   info_for_searching[4], info_for_searching[2], 1,
                                                   offset)   # 1 - "не женат (не замужем)"
                    create_database()
                    checking_profiles = add_profiles(profiles)
                    counter_data = self.viewing_profile(checking_profiles, counter, event.user_id, offset)
                    add_key = counter_data[2]
                    profile_name = counter_data[3]
                    profile_id = counter_data[4]

                elif event.text.lower() == 'поиск' or event.text.lower() == 'search' or event.text.lower() == 's' and search_key == 1:
                    self.send_message(event.user_id, 'Для продолжения поиска используй команду Далее (Next, n)!')

                elif event.text.lower() == 'далее' or event.text.lower() == 'next' or event.text.lower() == 'n':
                    if counter_data != 0:
                        counter = counter_data[0]
                        offset = counter_data[1]
                        if counter == -1 and offset != 0 and offset % 10 == 0:
                            profiles = backbot.user_search(info_for_searching[1], info_for_searching[3],
                                                           info_for_searching[4], info_for_searching[2], 1,
                                                           offset)  # 1 - "не женат (не замужем)"
                            checking_profiles = add_profiles(profiles)
                        counter_data = self.viewing_profile(checking_profiles, counter, event.user_id, offset)
                        add_key = counter_data[2]
                        profile_name = counter_data[3]
                        profile_id = counter_data[4]
                    else:
                        self.send_message(event.user_id, 'Поиск надо начинать с команды Поиск (Search, S)!')

                elif event.text.lower() == 'лучшие' or event.text.lower() == 'best' or event.text.lower() == 'b':
                    best_profiles = get_best_profiles()
                    if not best_profiles:
                        self.send_message(event.user_id, 'У тебя ещё нет сохранённых анкет.')
                    else:
                        self.send_message(event.user_id, f'Список сохранённых анкет:')
                        for b_profile in best_profiles:
                            p_name = b_profile['name']
                            p_id = b_profile['id']
                            self.send_message(event.user_id, f'{p_name} https://vk.com/id{p_id}')

                elif event.text.lower() == 'добавить' or event.text.lower() == 'add' or event.text.lower() == 'a' and add_key == 0:
                    self.send_message(event.user_id, 'Пока нет анкеты, которую можно было бы добавить в Лучшие.')

                elif event.text.lower() == 'добавить' or event.text.lower() == 'add' or event.text.lower() == 'a' and add_key == 1:
                    text = add_best_profile(profile_id, profile_name)
                    self.send_message(event.user_id, f'{text}')

                else:
                    self.send_message(event.user_id, 'Я не знаю такую команду, повтори, пожалуйста.')


if __name__ == '__main__':
    bot = FrontBot(bottoken)
    backbot = BackBot(mytoken)
    bot.handler()
