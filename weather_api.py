import requests
from settings import weather_api_key
from geocoder import get_coordinates

headers = {"X-Yandex-API-Key": weather_api_key}

translation = requests.get('https://api.weather.yandex.ru/v1/translations?lang=ru_RU', headers=headers).json()


def get_weather(place):
    api_server = "https://api.weather.yandex.ru/v1/forecast?"

    coord = get_coordinates(place)

    forecast = []

    params = {
        'lat': coord[1],
        'lon': coord[0],
        'lang': 'ru_RU'
    }

    response = requests.get(api_server, headers=headers, params=params)
    json_response = response.json()
    now_weather = json_response['fact']
    future_weather = json_response['forecasts']
    forecast.append({'temp': now_weather['temp'],
                     'feels_like': now_weather['feels_like'],
                     'condition': translation[now_weather['condition']],
                     'date': 'сегодня'})

    for i in range(1, 4):
        _weather = {}
        _weather['date'] = future_weather[i]['date']
        _weather['temp'] = future_weather[i]['parts']['day']['temp_avg']
        _weather['feels_like'] = future_weather[i]['parts']['day']['feels_like']
        _weather['condition'] = translation[future_weather[i]['parts']['day']['condition']]
        forecast.append(_weather.copy())

    return forecast