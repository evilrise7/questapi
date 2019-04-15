# Библиотеки
from flask import Flask, request
import math
import json
import logging
import requests


# Инициализация навыка и логгирование
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Данные о пользователе
sessionStorage = {}

# Считываем инфу из файла с диалогами
with open("quotes.json", "rt", encoding="utf8") as f:
    quotes = json.loads(f.read())


# Класс для работы со всем, что связано с картами
class MapsAPI:
    global search_api_server, api_key, geo_req

    def __init__(self):
        # Для поиска объектов
        self.search_api_server = "https://search-maps.yandex.ru/v1/"
        self.api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
        self.geo_req = "https://geocode-maps.yandex.ru/1.x/?geocode={}&format=json"

    # Информация о городах
    def geocode_obj(self, obj, kind):
        # Статус обработки запроса
        request = None
        # Запрос
        geocoder_request = self.geo_req.format(obj)
        try:
            response = requests.get(geocoder_request)
            if response:
                json_response = response.json()
                toponym = json_response["response"]["GeoObjectCollection"]
                toponym_feature = toponym["featureMember"][0]["GeoObject"]

                # Если речь идет о поиски координатов города
                if not kind:
                    coordinates = toponym_feature["Point"]["pos"]
                    return coordinates

            # Обработка ошибки запроса
            else:
                print("SEARCH_ERROR")
                print(geocoder_request)
                print("HTTP_ERR ",
                      response.status_code, "(", response.reason, ")")
                return 0

        # Обработка ошибки при потерянном соединении с интернетом
        except Exception:
            print("INTERNET_CONNECTION_ERROR")
            print(geocoder_request)
            return 0

    # Поиск объектов
    def search_obj(self, city, obj):
        # Адрес города, где происходят события
        address_ll = self.geocode_obj(city, 0)
        search_params = {
            "apikey": self.api_key,
            "text": str(obj),
            "lang": "ru_RU",
            "ll": address_ll,
            "type": "biz"
        }

        # Ответ от найденного объекта
        response = None
        try:
            response = requests.get(self.search_api_server, params=search_params)
            if response:
                json_response = response.json()
                # Получаем первую найденную организацию.
                organization = json_response["features"][0]

                # Получаем координаты ответа.
                point1 = organization["geometry"]["coordinates"]
                org_point = "{0}, {1}".format(point1[0], point1[1])

                return 1

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
        return str(round(distance, 0))[:-2]


# Класс для передачи информации из JSON в диалог
class Dialogue:
    global quotes

    def __init__(self):
        # Текущая глава и концовка
        self.chapter = 1
        self.question = 1
        self.step = 0  # Отступ по иерархии в JSON. Подтипы [[0], [[1]]]
        self.begin = True  # Перейти в начало главы
        self.ending = False

    # Работа с выбором реплик из JSON
    def response_dialogue(self, chapter, begin, step, ending):
        # Текст подачи от навыка
        text = ""
        # Взять название главы из JSON
        begin_txt = quotes[str(self.chapter)]["name"]
        # Если мы перешли в начало главы
        if begin:
            # Текст оглавления
            text = "Глава {}: {}\n".format(self.chapter, begin_txt)

            # Часть диалога от навыка
            person_txt = quotes[str(
                self.chapter)]["quotes"][str(self.question)][str(step)]

            text = text + person_txt
        return text

    # Сброс значений
    def reset(self):
        self.chapter = 1
        self.question = 1
        self.step = 0
        self.begin = True
        self.ending = False


# Создаю объекты классов
maps = MapsAPI()  # Для карт
dialog = Dialogue()  # Для диалогов

# Для главы 2
picked_address_2 = None


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
    global maps, dialog
    # Иницализация пользователя в сессиии
    user_id = req['session']['user_id']

    # Если пользователь новый, то начнем с первой главы
    if req['session']['new']:
        # Настройки для класса
        dialog.reset()

        chapter_txt = dialog.response_dialogue(
            dialog.chapter, dialog.begin, dialog.step, dialog.ending)

        res['response']['text'] = chapter_txt
        return


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


# Запуск игры
if __name__ == '__main__':
    app.run()
