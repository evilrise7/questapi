# Библиотеки
from flask import Flask, request
import os
import math
import json
import random
import logging
import requests
import wikipedia


# Инициализация навыка и логгирование
app = Flask(__name__)
app.config['SECRET_KEY'] = 'oh_so_secret'
logging.basicConfig(level=logging.INFO)
# Для медиа в API
token = "AQAAAAAgJxqBAAT7o_igAfUDAkY3pzREDfFKi0k"

# Данные о пользователе
sessionStorage = {}

# Команды для теста глав
cmd = ["/chapter1", "/chapter2", "/chapter3", "/chapter4",
       "/chapter5", "/chapter6", "/глава1", "/глава2",
       "/глава3", "/глава4", "/глава5", "/глава6"]

# Считываем инфу из файла с диалогами
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
dialogues = os.path.join(THIS_FOLDER, 'quotes.json')
endings = os.path.join(THIS_FOLDER, 'endings.json')

# Диалоги из JSON
with open(dialogues, "rt", encoding="utf8") as f:
    quotes = json.loads(f.read())

# Концовки из JSON
with open(endings, "rt", encoding="utf8") as f:
    ends = json.loads(f.read())


# Класс для работы со всем, что связано с картами
class MapsAPI:
    def __init__(self):
        # Для поиска объектов
        self.search_api_server = "https://search-maps.yandex.ru/v1/"
        self.api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

    # Поиск объектов
    def search_obj(self, coordinates, obj):
        # Адрес города, где происходят события
        search_params = {
            "apikey": self.api_key,
            "text": str(obj),
            "lang": "ru_RU",
            "ll": coordinates,
            "type": "biz"
        }

        # Ответ от найденного объекта
        response = None
        try:
            response = requests.get(
                self.search_api_server, params=search_params)
            if response:
                json_response = response.json()
                # Получаем первую найденную организацию.
                organization = json_response["features"][0]

                # Получаем координаты ответа.
                point1 = organization["geometry"]["coordinates"]
                org_point = (point1[0], point1[1])
                return org_point

            # Обработка ошибки запроса
            else:
                print("SEARCH_ERROR")
                print("HTTP_ERR ",
                      response.status_code, "(", response.reason, ")")
                return 0

        # Обработка ошибки с интернет соединением
        except Exception:
            print("INTERNET_CONNECTION_PROBLEM")
            return 0

    # Определяем функцию, считающую расстояние между двумя точками
    def lonlat_distance(self, a, b):
        degree_to_meters_factor = 111 * 1000  # 111 километров в метрах
        a_lon, a_lat = a
        b_lon, b_lat = b

        # Берем среднюю по широте точку и считаем коэффициент для нее.
        radians_lattitude = math.radians((a_lat + b_lat) / 2.)
        lat_lon_factor = math.cos(radians_lattitude)

        # Вычисляем смещения в метрах по вертикали и горизонтали.
        dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
        dy = abs(a_lat - b_lat) * degree_to_meters_factor

        # Вычисляем расстояние между точками.
        distance = math.sqrt(dx * dx + dy * dy)

        # Возвращаем длину пути
        return round(distance, 0)

    # Найдем кафе для Главы 2
    def find_cafe(self, cafe):
        # События происходят в киностудии
        # взял для примера Paramount Pictures
        studio_corstr = "-118.317346, 34.08446"
        studio_cortup = (-118.317346, 34.08446)
        # Берем координаты места действия
        if self.search_obj(studio_corstr, cafe.lower()):
            place_cor = self.search_obj(studio_corstr, cafe.lower())
        else:
            return 0

        # Если требования соблюдены, и кафе в радиусе 2 км, возвращаем
        # Положительный ответ. Иначе 0
        if self.lonlat_distance(place_cor, studio_cortup) <= 2000:
            return 1
        else:
            return 0


maps = MapsAPI()  # Для карт


# Класс для передачи информации из JSON в диалог
class Dialogue:
    global quotes, sessionStorage, maps, ends

    def __init__(self):
        # Текущая глава и концовка
        self.chapter = 0
        self.question = 1
        self.step = 0  # Отступ по иерархии в JSON.
        self.under = 0  # Отступ по иерархии в JSON. Подтипы [[0], [[1]]]
        self.begin = True  # Перейти в начало главы
        self.ending = 0

    # Работа с выбором реплик из JSON
    def response_dialogue(self):
        # Текст подачи от навыка
        text = ""
        # Если мы перешли в начало главы
        if self.begin:
            # Часть диалога от навыка
            person_txt = quotes[str(self.chapter)]["quotes"][str(
                self.question)][0][self.step]

            # Запись текста
            text = quotes[str(
                self.chapter)]["person"] + ":\n-" + person_txt

        # Если мы перешли в конец 1
        elif self.ending:
            end_txt = ends[str(self.ending)]["text"]
            return end_txt

        # При продолжении текущего диалога в текущей главе
        else:
            # Берем лист всех вариантов вопроса в игроку
            person_list = quotes[str(self.chapter)]["quotes"][str(
                self.question)][0]

            # Если вариантов вдруг меньше, чем самих вопросов
            # То изменяем шаг по иерархии
            if len(person_list) - 1 < self.step:
                person_txt = person_list[len(person_list) - 1]
            else:
                person_txt = person_list[self.step]

            # Если внутри вопроса есть подвопрос
            if any(isinstance(i, list) for i in person_list):
                iter_list = person_list[self.step]
                # Если вариантов вдруг меньше, чем самих вопросов
                # То изменяем шаг по иерархии
                if len(iter_list) - 1 < self.under:
                    person_txt = iter_list[len(iter_list) - 1]
                else:
                    # Записываем текст
                    person_txt = iter_list[self.under]

            # Запись текста
            text = quotes[str(
                self.chapter)]["person"] + ":\n-" + str(person_txt)
        return text

    # Если дошли до части, где мы называем ребенка
    def name_sharlotta(self, user_id, req):
        # Берем лист всех вариантов вопроса в игроку
        person_list = quotes[str(self.chapter)]["quotes"]["5"][0]

        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            return str(quotes[str(
                self.chapter)]["person"]) + ":\n-" + str(
                person_list[0])

        # если нашли, то захватываем с собой
        else:
            sessionStorage[user_id]['first_name'] = first_name
            return str(quotes[str(
                self.chapter)]["person"]) + ":\n-" + str(
                person_list[-1].format(first_name.title()))

    # Поиск кафе для Главы 2
    def get_cafe(self, user_id, req):
        # Берем лист всех вариантов вопроса в игроку
        person_list = quotes[str(self.chapter)]["quotes"]["3"][0][0]
        cafe_name = req['request']['original_utterance'].lower()

        # Если кафе выполняет требования заданные персонажем
        if maps.find_cafe(cafe_name):
            sessionStorage[user_id]['cafe_name'] = cafe_name.title()
            # Сохраняем в session и возвращаем сообщение
            return str(quotes[str(
                self.chapter)]["person"]) + ":\n-" + str(
                person_list[0])
        # Иначе
        else:
            # Возвращаем сообщение персонажа
            return str(quotes[str(
                self.chapter)]["person"]) + ":\n-" + str(
                person_list[-1])

    # Захватить ответы из JSON файла
    def get_suggests(self):
        # Забираем список предложенных ответов
        sug_list = quotes[str(
            self.chapter)]["quotes"][str(self.question)][-1]

        # Если список предложенных ответов имеет вложенные списки
        if any(isinstance(i, list) for i in sug_list):
            iter_list = sug_list[self.step]
            # Отмечаю, что это был подлист
            iter_list.append("-1")
            return iter_list

        # Вовзращаем предложенные варианты
        return sug_list

    # Проверка на конец диалога в текущей главе
    def check_end(self):
        question_list = quotes[str(
            self.chapter)]["quotes"][str(self.question)]

        # При завершении главы ставится внутри JSON - "q"
        for sub_question in question_list:
            # Если внутри текущего вопроса существуют подлисты
            # то идет проверка этих листов на наличие - "q"
            if any(isinstance(i, list) for i in sub_question):
                # Аналогично, проверка подлистов внутри листов
                for i in range(len(sub_question)):
                    for sub_element in range(len(sub_question[i])):
                        if sub_question[i][sub_element] == "q":
                            # Сброс настроек диалога и переход
                            # на следующую главу
                            self.reset()
                            self.chapter += 1
                            return 1

            # Если внутри нет подлистов, то считывается
            # текущий лист вопроса
            else:
                for element in range(len(sub_question)):
                    if sub_question[element] == "q":
                        # Сброс настроек диалога и переход
                        # на следующую главу
                        self.reset()
                        self.chapter += 1
                        return 1
        '''
        Проверка идет for циклом, а не itertools, zip, filter
        т.к. проверка занимает в одном цикле ~0.5 с
        В других же случаях: itertools ~1.1 с и т.д.
        '''
        return 0

    # Сброс значений
    def reset(self):
        self.question = 1

        self.begin = True
        self.ending = 0

        self.step = 0
        self.under = 0


# Класс для передачи информации о ножах
class WikipediaAPI:
    def __init__(self):
        # Настраиваю лист ножей
        self.index = 0
        self.weapon_list = ["Нож разведчика",
                            "Финка",
                            "Керамбит"]
        # Перемешиваю рандомно лист
        self.weapon_list = random.shuffle(self.weapon_list)

    def get_weapon_info(self):
        # Настраиваю язык для WIKIPEDIA API
        wikipedia.set_lang("ru")
        # Вывожу только основное введение об оружии и возвращаю его
        info = wikipedia.summary(self.weapon_list[self.index], sentences=3)
        return info


# Создаю объекты классов
dialog = Dialogue()  # Для диалогов
wiki = WikipediaAPI()  # Для википедии(ножи)


# Тело навыка
@app.route('/post', methods=['POST'])
def main():
    # Логирование
    logging.info('Request: %r', request.json)
    # Форма ответа
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    # Отправляем ответы и запросы в функцию
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    # Записываем полученный ответ в JSON файл
    return json.dumps(response)


# Поддерживание диалога с пользователем
def handle_dialog(res, req):
    global maps, dialog, quotes, cmd
    # Иницализация пользователя в сессиии
    user_id = req['session']['user_id']

    # Если пользователь новый, то начнем с первой главы
    if req['session']['new']:
        # Очистка словаря от данных
        sessionStorage.clear()
        # Настройки для класса
        dialog.reset()
        dialog.chapter = 0
        res = new_chapter(res, user_id)
        return

    # Если мы не завершили игру, можно показать подсказки
    if not dialog.ending:
        # Взять текущие предложенные ответы и перевести их в строчные
        sug_list = dialog.get_suggests()
        sug_list = list(map(lambda i: i.lower(), sug_list))

    # Если мы в Главе 1, дошли до части, где называем ребенка
    if not dialog.ending and write_suggests(user_id) == "name":
        # Берем часть диалога об имени Шарлотты
        data_res = dialog.name_sharlotta(user_id, req)

        # Сбрасываем настройки диалога к следующей главе
        dialog.reset()
        dialog.chapter = 2
        res = chapter_object(data_res, res, user_id)
        return

    # Если мы в Главе 2, дошли до части, где называем кафе
    if not dialog.ending and write_suggests(user_id) == "cafe":
        # Если мы не берем подсказку
        if req['request']['original_utterance'].lower() \
                not in 'самые близкие кафе':
            data_res = dialog.get_cafe(user_id, req)

            # Сбрасываем настройки диалога к следующей главе
            dialog.reset()
            dialog.chapter = 3
            res = chapter_object(data_res, res, user_id)
            return

        # Если мы уже спросили про близкие кафе, теперь просим
        # Пользователя назвать его
        else:
            res['response']['text'] = error_check(res, "name_cafe")
            return

    # Команды для админа, для перехода между главами(debug)
    if req['request']['original_utterance'].lower() in сьв:
        dialog.reset()
        dialog.chapter = -1
        dialog.chapter = int(
            req['request']['original_utterance'].lower()[-1])
        res = new_chapter(res, user_id)
        return

    # Хотим сыграть еще раз в игру
    if req['request']['original_utterance'].lower() in 'сыграть еще раз!':
        dialog.reset()
        dialog.chapter = 1
        res = new_chapter(res, user_id)
        return

    # Остальные случаи
    if not dialog.ending and req['request']['original_utterance'].lower() \
            in sug_list:
        # Мы не в начале диалога, поэтому убираем эту опцию
        dialog.begin = False

        # Перевод сообщения от пользователя в строчный вариант
        sug_index = sug_list.index(
            req['request']['original_utterance'].lower())

        # Если уже конец главы, переходим на следующую
        if dialog.check_end() and dialog.chapter != 2:
            res = chapter_end(res, user_id, 0)
            return

        # Переход к следующему вопросу
        dialog.question += 1

        # Проверка на подлисты внутри ответов
        if "-1" in dialog.get_suggests():
            # Пользователь выбрал ответ, теперь меняем вопрос и подответ
            dialog.under = sug_index

            # В случае Главы 2, где нас требуют выбрать кафе для ужина
            if dialog.chapter == 2:
                if dialog.question == 2:
                    dialog.step = sug_index

            # В случае Главы 6, где нам требуется выбрать исход событий
            if dialog.chapter == 6:
                if dialog.question == 3 or dialog.question == 3:
                    dialog.step = sug_index

        # И наоборот
        else:
            dialog.step = sug_index

        '''
        Для первой главый ограничение в обновлении, т.к. там есть вводы
        '''
        if dialog.chapter == 0:
            if dialog.question == 5:
                # Если уже конец главы, переходим на следующую
                if dialog.check_end():
                    # Выводим ответ от навыка
                    res = chapter_end(res, user_id, 0)
                    return

        if dialog.chapter == 1:
            if dialog.question == 4 and dialog.step != 1:
                # Если уже конец главы, переходим на следующую
                if dialog.check_end():
                    # Выводим ответ от навыка
                    res = chapter_end(res, user_id, 0)
                    return

        '''
        Для второй главы, при завершении диалога мы идем в концовку 1
        '''
        if dialog.chapter == 2:
            if dialog.question == 4:
                # Если уже конец главы, переходим на следующую
                if 'cafe_name' not in sessionStorage[user_id]:
                    if dialog.check_end():
                        # Выводим ответ от навыка
                        res = chapter_end(res, user_id, 1)
                        return

        # Выводим ответ от навыка
        res['response']['text'] = dialog.response_dialogue()

        # Заполняем предложенные ответы
        # Если просили дать ответ с клавиатуры, подсказок нет
        if write_suggests(user_id):
            # Чтобы пользователю было легче, подсказываем ему
            # Самые близкие кафе
            if write_suggests(user_id) == "cafe":
                res = error_check(res, "map_cafe")
            return

        # Иначе они могут быть
        else:
            # Вывод подсказок после вопроса
            res['response']['buttons'] = get_suggests(user_id)
        return

    if dialog.ending:
        res['response']['text'] = error_check(res, "end")
        return

    # В случае, если были взяты не те подсказки,
    # пользователю дают по шее и просят выбрать одну из них
    res['response']['text'] = error_check(res, "request_text")

    # Вывод подсказок после вопроса
    res['response']['buttons'] = get_suggests(user_id)


# Начинаем новую главу
def new_chapter(res, user_id):
    # Заполняем предложенные ответы
    write_suggests(user_id)

    # Захват названия главы
    chapter_txt = dialog.response_dialogue()

    # Установка картинки и описания действия
    res = set_card(res)
    res['response']['card']['description'] = chapter_txt

    res['response']['text'] = chapter_txt
    # Вывод названия главы, персонажа и подсказок
    res['response']['buttons'] = get_suggests(user_id)

    # Обновляем игровое начало, т.к. мы уже в продолжении игры
    dialog.begin = False
    return res


# Если речь идет об именах или поиском объекта
def chapter_object(data_res, res, user_id):
    # Добавляем речь героев из следующей главы
    data_res += "\n" + dialog.response_dialogue()

    # Установка картинки
    res = set_card(res)
    res['response']['card']['description'] = data_res
    res['response']['text'] = data_res

    # Добавляем подсказки для следующей главы
    write_suggests(user_id)
    res['response']['buttons'] = get_suggests(user_id)
    return res


# Если главе наступил конец
def chapter_end(res, user_id, kind):
    response_text = ""

    dialog.check_end()

    # Для главы 2, где мы не идем в кафе
    if kind:
        # Заканчиваем игру концовкой 1
        dialog.chapter = -1
        dialog.begin = False
        dialog.ending = kind

        # Добавляем речь героев из следующей главы
        response_text = dialog.response_dialogue()
        res['response']['text'] = response_text
        return

    # Добавляем речь героев из следующей главы
    response_text += "\n" + dialog.response_dialogue()

    # Установка картинки
    res = set_card(res)
    res['response']['card']['description'] = response_text

    # Добавляем подсказки для следующей главы
    write_suggests(user_id)
    res['response']['buttons'] = get_suggests(user_id)

    res['response']['text'] = response_text
    return res


# Даем имя Шарлотте
def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


# Запись внутри сессии предложенные ответы
def write_suggests(user_id):
    writed_list = dialog.get_suggests()

    # Лист объектов, которые вводят с клавиатуры
    list_objects = ["name", "cafe"]

    # Проверка, нужно ли что-нибудь писать на клавиатуре
    for i in range(len(list_objects)):
        if list_objects[i] in writed_list:
            return list_objects[i]

    # Если это был подтип листа, то удаляем эти единички
    if "-1" in writed_list:
        writed_list = list(filter("-1".__ne__, writed_list))

    # Заполняем предложенные ответы
    sessionStorage[user_id] = {
        'suggests': writed_list
    }
    return 0


# Функция возвращает две подсказки для ответа.
def get_suggests(user_id):
    session = sessionStorage[user_id]

    # Выбираем две первые подсказки из массива.
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests']
    ]

    return suggests


# При наличии ошибок
def error_check(res, error):
    bot_txt = ""
    # Если ошибка была из-за неправильно введенных данных
    if error == "request_text":
        bot_txt = "☻Навык:\n-Нажмите на одну из подсказок!"

    # Если нам нужно открыть карту с кафе
    if error == "map_cafe":
        suggests = [{
            "title": "Самые близкие кафе",
            "url": str(quotes["2"]["url"]),
            "hide": True
        }]
        res['response']['buttons'] = suggests
        return res

    # Если просмотрели кафе, то пишем его в навык
    if error == "name_cafe":
        bot_txt = "☻Навык:\n-Теперь, назовите кафе!"

    # Если мы завершили игру и хотим еще раз сыграть
    if error == "end":
        bot_txt = "☻Навык:\n-Хотите сыграть еще?" + \
                  "\nНапишите мне: 'Сыграть еще раз!'"

    # Возвращаем сообщение от навыка
    return bot_txt


# Установка картинки
def set_card(res):
    res['response']['card'] = {}
    res['response']['card']['type'] = "BigImage"
    res['response']['card']['title'] = quotes[str(
        dialog.chapter)]["name"]
    res['response']['card']['image_id'] = quotes[str(
        dialog.chapter)]["image"]
    return res


# Запуск игры
if __name__ == '__main__':
    app.run()
