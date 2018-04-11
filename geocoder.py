# coding:utf-8

import requests
import sys

from settings import apikey

def geocode(address):
    # Собираем запрос для геокодера.
    geocoder_request = "http://geocode-maps.yandex.ru/1.x/?geocode={address}&format=json".format(**locals())

    # Выполняем запрос.
    response = requests.get(geocoder_request)

    if response:
        # Преобразуем ответ в json-объект
        json_response = response.json()
    else:
        raise RuntimeError(
            """Ошибка выполнения запроса:
            {request}
            Http статус: {status} ({reason})""".format(
            request=geocoder_request, status=response.status_code, reason=response.reason))

    # Получаем первый топоним из ответа геокодера.
    # Согласно описанию ответа он находится по следующему пути:
    features = json_response["response"]["GeoObjectCollection"]["featureMember"]
    return features[0]["GeoObject"] if features else None


# Получаем координаты объекта по его адресу.
def get_coordinates(address):
    toponym = geocode(address)
    if not toponym:
        return (None,None)
    
    # Координаты центра топонима:
    toponym_coodrinates = toponym["Point"]["pos"]
    # Широта, преобразованная в плавающее число:
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
    return float(toponym_longitude), float(toponym_lattitude)


# Получаем параметры объекта для рисования карты вокруг него.
def get_ll_span(address, org_addresses, list_org_addresses):
    toponym1 = geocode(address)
    if not toponym1:
        return (None,None)
    # Координаты центра топонима:
    toponym_coodrinates = toponym1["Point"]["pos"]
    # Долгота и Широта :
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

    ll = None
    if len(org_addresses)==1:
        toponym2 = geocode(list_org_addresses[0])
        if toponym2:
            lon1, lat1 = org_addresses[0].split(',')
            toponym_lattitude, toponym_longitude = float(toponym_lattitude), float(toponym_longitude)
            lat1, lon1 = float(lat1), float(lon1)
            a = max(toponym_longitude,lon1)
            b = min(toponym_longitude,lon1)
            a2 = max(toponym_lattitude, lat1)
            b2 = min(toponym_lattitude, lat1)
            ll = ",".join([str(min(toponym_longitude, lon1)+(a-b)/2), str(min(toponym_lattitude, lat1)+(a2-b2)/2)])

            # Рамка вокруг объекта:
            envelope1 = toponym1["boundedBy"]["Envelope"]
            envelope2 = toponym2["boundedBy"]["Envelope"]

            # левая, нижняя, правая и верхняя границы из координат углов:
            l_, b_ = envelope1["lowerCorner"].split(" ")
            r_, t_ = envelope1["upperCorner"].split(" ")

            _l, _b = envelope2["lowerCorner"].split(" ")
            _r, _t = envelope2["upperCorner"].split(" ")
            print(l_, b_, r_, t_)
            print(_l, _b, _r, _t)
            l, b = min(l_, _l),  min(b_, _b)
            r, t = max(r_, _r), max(t_, _t)

    else:
        ll = ",".join([toponym_longitude, toponym_lattitude])

        envelope1 = toponym1["boundedBy"]["Envelope"]

        # левая, нижняя, правая и верхняя границы из координат углов:
        l, b = envelope1["lowerCorner"].split(" ")
        r, t = envelope1["upperCorner"].split(" ")

    if len(org_addresses)>1:
        list_x_coordinates = []
        list_y_coordinates = []

        for ll in org_addresses:

            d_org, sh_org = ll.split(",")
            d_org = float(d_org)
            d_org += 0.1
            d_org = str(d_org)

            list_x_coordinates.append(d_org)
            list_y_coordinates.append(sh_org)

        x1 = max(max(list_x_coordinates), l, r)
        y1 = max(max(list_y_coordinates), t, b)

        x2 = min(min(list_x_coordinates), l, r)
        y2 = min(min(list_y_coordinates), t, b)

    else:

        x1 = max(l, r)
        y1 = max(t, b)

        x2 = min(l, r)
        y2 = min(t, b)
  
    # Вычисляем полуразмеры по вертикали и горизонтали
    dx = abs(float(x1) - float(x2)) / 2.0
    dy = abs(float(y1) - float(y2)) / 2.0

    # Собираем размеры в параметр span
    span = "{dx},{dy}".format(**locals())

    return (ll, span)

# Находим ближайшие к заданной точке объекты заданного типа.
def get_nearest_object(point, kind):
    geocoder_request_template = "http://geocode-maps.yandex.ru/1.x/?geocode={ll}&kind={kind}&format=json"
    ll = "{0},{1}".format(point[0], point[1])

    # Выполняем запрос к геокодеру, анализируем ответ.
    geocoder_request = geocoder_request_template.format(**locals())
    response = requests.get(geocoder_request)
    if not response:
        raise RuntimeError(
            """Ошибка выполнения запроса:
            {geocoder_request}
            Http статус: {status} ({reason})""".format(
            request=geocoder_request, status=response.status_code, reason=response.reason))

    # Преобразуем ответ в json-объект
    json_response = response.json()
    
    # Получаем первый топоним из ответа геокодера.
    features = json_response["response"]["GeoObjectCollection"]["featureMember"]
    return features[0]["GeoObject"]["name"] if features else None


def poisk(address_ll, hobby, num = 1):
    try:
        search_api_server = "https://search-maps.yandex.ru/v1/"

        search_params = {
            "apikey": apikey,
            "text": hobby,
            "lang": "ru_RU",
            "ll": address_ll, # адрес дома
            "type": "geo,biz"
        }

        response = requests.get(search_api_server, params=search_params)
    except:
        print("Запрос не удалось выполнить. Проверьте наличие сети Интернет.")
        sys.exit(1)

    coordinates = None
    working_time = None
    # Преобразуем ответ в json-объект
    json_response = response.json()
    for k in range(num):
        organization = json_response["features"][k]["properties"]["CompanyMetaData"]
        org_time_work = organization["Hours"]['Availabilities']
        if 'TwentyFourHours' in org_time_work[0]:
            color='pmgns'
        elif 'Intervals' in org_time_work[0]:
            color='pmbls'
        else:
            color='pmgrs'
        coordinate_x, coordinate_y = json_response["features"][k]["geometry"]["coordinates"]
        org_point = "{0},{1}".format(coordinate_x, coordinate_y)
        coordinates = org_point
        working_time = color

    return coordinates, working_time

def search(city, org, num = 1):
    try:
        search_api_server = "https://search-maps.yandex.ru/v1/"
        ll = '{},{}'.format(*get_coordinates(city))
        search_params = {
            "apikey": apikey,
            "text": org,
            "lang": "ru_RU",
            "ll": ll,
            "type": "geo,biz"
        }

        response = requests.get(search_api_server, params=search_params)
    except:
        print("Запрос не удалось выполнить. Проверьте наличие сети Интернет.")
        sys.exit(1)

    organizations = []
    # Преобразуем ответ в json-объект
    json_response = response.json()
    for i in range(num):
        try:
            organization = json_response["features"][i]["properties"]["CompanyMetaData"]
            try:
                url = organization['url']
            except:
                url = 'Сайт не обнаружен.'
            org_name, _org_address = organization["name"], organization["address"].split(', ')

            org_address = []
            for _ in _org_address:
                if _ not in org_address:
                    org_address.append(_)
            org_address = ', '.join(org_address)

            _1 = '{}, {}. {}'.format(org_name, org_address, url)
            point = json_response["features"][i]["geometry"]["coordinates"]
            org_point = "{0},{1}".format(point[0], point[1])
            organizations.append([_1, org_point])
        except:
            print('колличество организаций меньше. ', 'Искал: ', org,'.')
            return organizations
    return organizations