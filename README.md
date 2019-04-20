# Cruel to be Kind
![](logo.png)
## Описание навыка
Съемочная площадка становится свидетелями убийства семьи известного режиссера. Им предстоит доказать свою невиновность и поймать убийцу.
## Описание работы навыка
Навык предлагает сыграть в интерактивное кино. Он имеет заложенный сценарий, где пользователь будет выполнять роль одного из главных героев. Как поведет себя пользователь во время прохождения, будет влиять и на концовку игры.
## Сделано
```
Все главы
Все концовки
JSON файлы с концовками и главами
WikipediaAPI
StaticMapsAPI
GeocoderHTTP
Работа с Алисой
YANDEX.FIO
MovieAPI
```
## Не сделано
```
Презентация
```
## Планы на API
```
MovieAPI
MusicAPI
StaticMapsAPI
Yandex.MarketHTTP
GeocoderHTTP
WikipediaHTTP(или любой другой ресурс, как энциклопедия)
```
## Планы на проект
```
Интеркативное кино, но диалоговое
Сделать немного иллюстраций, чтобы пользователь не запутался в происходящем
Начать кодить
Насилие, жестокость и все, что может помешать модерации XD
```
## Главные герои
```
Джейкоб - киноактер, играет в романах, пробовался в вестернах.
Мэйсон - каскадер Джейкоба.
Ава - старшая дочь Джейкоба
Мия - младшая дочь Джейкоба
Томас - режиссер. Ставит фильм в той же студии, где снимается Джейкоб.
Маргарита - жена Томаса.
Шарлотта - дочь Маргариты. Еще не родилась.
Коннор - детектив.
Уильям - убийца
```
## Сценарий
Сценарий написан автором проекта. Сценарий доступен только преподователю курса. Сценарий может не совпадать с написанным в проекте, т.к. проект представляет сжатый вариант полноценного сценария. Многие вещи из полноценного были выброшены в далекий космос, прямо к Тесла, т.к. не имеют в себе смысла и работы с API
```
Размер сценария - 19 СТР.
Главы: 9/9
Концовок: 7
Статус: Завершен
```
## Библиотеки и работа с API
## Для работы с PythonAnyWhere
```
1)Необходимо изменить название главного файла api.py на flask_app.py при загрузке на сервер
2)При прохождении игры в Главе 2, где вас просят назвать кафе, называйте самые близкие кафе, которые найдете от адреса -118.317346, 34.08446. Иначе, класс MapsApi будет в поисках дальнего кафе, тем самым runtime будет больший, из-за интернет соединения между сервером PythonAnyWhere и YandexStaticMaps. При долгом runtime, webhook выведет ошибку, что сервер не ответил за заданное время(1.5 с - это максимум). Поэтому выбирайте близкие, например: 7-Eleven, KFC и т.д.
3)Если вы работаете с проектом в системе PythonAnyWhere, то вам необходимо запустить BASH консоль и скачать следующие библиотеки по командам
```
```
Насчет картинок:
они вписываются в "image" внутри "quotes.json"
Глава 1 - 1.png
Глава 2 - 2.png
Глава 3 - 3.png
Глава 4 - 31.png
Глава 5 - 32.png
Глава 6 - 4.png
```
```
(здесь рассматриваются именно библиотеки какой-то API)
(все остальные библиотеки либо входят внутри сервера, либо устанавливаются тем же способом, что и API библиотека)
```
```java
Wikipedia: pip3 install --user wikipedia
```
## Автор проекта
* **Nurmakhan Bakhtiyar** - *ULTRABAKHA* - [evil_rise7](https://github.com/evilrise7)
