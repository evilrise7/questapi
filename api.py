# Библиотеки
from flask import Flask, request
import math
import requests
import logging
import json


# Инициализация навыка и логгирование
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Данные о пользователе
sessionStorage = {}

# Для поиска объектов
search_api_server = "https://search-maps.yandex.ru/v1/"
api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
geo_req = "https://geocode-maps.yandex.ru/1.x/?geocode={}&format=json"

# Текущая глава и концовка
chapter = 1
ending = False

# Для главы 2
picked_address_2 = None


# Информация о городах
def geocode_obj(obj, kind):
    global geo_req
    # Статус обработки запроса
    request = None
    # Запрос
    geocoder_request = geo_req.format(obj)
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
            print("HTTP_ERR ", response.status_code, "(", response.reason, ")")
            return 0

    # Обработка ошибки при потерянном соединении с интернетом
    except Exception:
        print("INTERNET_CONNECTION_ERROR")
        print(geocoder_request)
        return 0


# Поиск объектов
def search_obj(city, obj):
    global picked_address_2

    # Адрес города, где происходят события
    address_ll = geocode_obj(city, 0)
    search_params = {
        "apikey": api_key,
        "text": str(obj),
        "lang": "ru_RU",
        "ll": address_ll,
        "type": "biz"
    }

    # Ответ от найденного объекта
    response = None
    try:
        response = requests.get(search_api_server, params=search_params)
        if response:
            json_response = response.json()
            # Получаем первую найденную организацию.
            organization = json_response["features"][0]

            # Получаем координаты ответа.
            point1 = organization["geometry"]["coordinates"]
            org_point = "{0}, {1}".format(point1[0], point1[1])

            picked_address_2 = org_point
            return 1

        # Обработка ошибки запроса
        else:
            print("SEARCH_ERROR")
            print("HTTP_ERR ", response.status_code, "(", response.reason, ")")
            return 0

    # Обработка ошибки с интернет соединением
    except Exception:
        print("INTERNET_CONNECTION_PROBLEM")
        return 0


# Определяем функцию, считающую расстояние между двумя точками
def lonlat_distance(a, b):
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
    global chapter

    # Иницализация пользователя в сессиии
    user_id = req['session']['user_id']

    # Если пользователь новый, то начнем с первой главы
    if req['session']['new']:
        chapter = 1
        return


# Запуск игры
if __name__ == '__main__':
    app.run()