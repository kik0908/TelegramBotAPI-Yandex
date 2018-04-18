from random import choice, shuffle
from itertools import cycle

import pymorphy2
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from geocoder import search, get_ll_span, get_coordinates
from weather_api import get_weather
from settings import TOKEN

places = {'спорт': ['стадион', 'дворец спорта', 'тренажёрный зал', 'бассейн'],
          'культура': ['театр', 'музей', 'библиотека', 'дом культуры'],
          'развлечения': ['клуб', 'кино', 'сауна', 'бар', 'караоке', 'квесты', 'боулинг', 'бильярдный зал', 'спортивно-тактические клубы'],
          'медицина': ['больница', 'поликлиника', 'стоматология', 'травмпункт'],
          'медтовары': ['аптека', 'медтовары'],
          'животные': ['Товары для животных', 'ветеренарная клиника'],
          'питание': ['кафе', 'ресторан', 'макдональдс', 'kfc', 'столовая', 'пиццерия', 'суши бар', 'банкетный зал'],
          'религия': ['православный храм', 'мечеть', 'собор'],
          'магазины': ['торговый центр', 'спорттовары', 'магазин одежды', 'детский магазин', 'канцтовары', 'книжный магазин'],
          'автосервис': ['штрафстоянка', 'шиномонтаж', 'заправка', 'автомойка', 'авторемонт', 'стоянка', 'автохимия', 'шины, диски'],
          'туризм': ['гостиница', 'хостел', 'отель', 'база отдыха', 'авиабилеты', 'железнодорожные билеты'],
          'прогулка': ['парк', 'сквер', 'экскурсии', 'достопримечательность', 'отдых'],
          }

reply_keyboard = [['Развлечения', 'Питание'],
                  ['Спорт', 'Религия', 'Туризм'],
                  ['Культура', 'Магазины'],
                  ['Автосервис', 'Медтовары', 'Медицина'],
                  ['Животные', 'Прогулка'],
                  ['Погода'],
                  ['Сменить город']]

inline_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Следующее место', callback_data=1)]])

inline_keyboard_1 = InlineKeyboardMarkup([[InlineKeyboardButton('Следующий день', callback_data=2)]])

inline_keyboard_2 = InlineKeyboardMarkup([[InlineKeyboardButton('Следующий день', callback_data=2)],
                                          [InlineKeyboardButton('Предыдущий день', callback_data=3)]])

location = {}
weather = {}

morph = pymorphy2.MorphAnalyzer()


def start(bot, update):
    update.message.reply_text("Привет! :)\n"
                              "Я твой бот-помощник!\n")
    update.message.reply_text("Я помогу тебе найти интересные места в городе на основе твоих интересов, а также узнать погоду.\n"
                              "Для этого напиши /guide\n"
                              "Для прекращения поиска набери  /stop\n")
    update.message.reply_text("Если захочешь узнать про пробки, то набери\n"
                              "/traffic_congestion {АДРЕС1}:{АДРЕС2}\n"
                              "или\n"
                              "/traffic_congestion {АДРЕС}\n")


def guide(bot, update):
    update.message.reply_text("Какой город тебя интересует?")
    return 1


def town(bot, update, user_data):
    user_data['locality'] = update.message.text
    _ans = search(user_data["locality"], 'кино')
    if not _ans:
        print('Ошибка при поиске города')
        update.message.reply_text("Прости, но я не смог найти такой город.\nКакой город тебя интересует?")
        return 1
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Выберите сферу которая вас интересует", reply_markup=markup)
    return 2

def stop(bot, update):
    update.message.reply_text("Удачи!")
    return ConversationHandler.END


def interests(bot, update, user_data):
    global location

    message = update.message.text.lower()
    if message == 'сменить город':
        return 1

    elif message == 'погода':
        _weather = get_weather(user_data['locality'])

        gr = morph.parse('градус')[0]
        degrise = str(_weather[0]['temp']) + ' ' + gr.make_agree_with_number(abs(int(_weather[0]['temp']))).word
        degrise1 = str(_weather[0]['feels_like']) + ' ' + gr.make_agree_with_number(
            abs(int(_weather[0]['feels_like']))).word
        date = _weather[0]['date']
        osh = _weather[0]['condition']

        mes = "Погода на {}.\nТемпература {}(ощущается как {}), {}".format(date, degrise, degrise1, osh)
        _1 = update.message.reply_text(mes, reply_markup=inline_keyboard_1)
        weather[_1.message_id] = [_weather, 0]

        return 2

    elif message in places:
        update.message.reply_text("Начинаю поиск...")

        _1 = 8  # choice(range(3, len(places[message]+1)))

        datas = []
        _text = []

        random_places = []

        for _ in range(len(places[message]), 0, -1):
            random_place = choice(places[message])
            while True:
                if random_place not in random_places:
                    break
                random_place = choice(places[message])

            result = search(user_data['locality'], random_place, _1)
            # print('Результат поиска: ', result)
            for _ in result:
                data = _[0]
                coord = _[1]

                if data not in datas:
                    static_api_request = "http://static-maps.yandex.ru/1.x/?ll={}&l=map&z=15&pt={},pm2blywm1".format(
                        coord, coord)
                    # print('Информация прошла проверку: ', data)
                    _text.append('[Картинка.]({})\n{} ({})'.format(static_api_request, data, random_place))
                    datas.append(data)

        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        shuffle(_text)

        _text = cycle(_text)
        _return = update.message.reply_text(next(_text), reply_markup=inline_keyboard)
        location[_return.message_id] = _text
        update.message.reply_text("Выберите сферу которая вас интересует", reply_markup=markup)

        return 2

    else:
        return 2


def change_places(bot, update):
    global location

    query = update.callback_query

    if query.data == '1':
        bot.edit_message_text(text=next(location[query.message.message_id]),
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id, parse_mode='markdown',
                              reply_markup=inline_keyboard)

    elif query.data == '2':
        weather[query.message.message_id][1] += 1
        _key_board = inline_keyboard_2

        if weather[query.message.message_id][1] >= len(weather[query.message.message_id][0]):
            weather[query.message.message_id][1] = 0
            _key_board = inline_keyboard_1

        _weather = weather[query.message.message_id][0]
        index = weather[query.message.message_id][1]
        gr = morph.parse('градус')[0]
        degrise = str(_weather[index]['temp']) + ' ' + gr.make_agree_with_number(abs(int(_weather[index]['temp']))).word
        degrise1 = str(_weather[index]['feels_like']) + ' ' + gr.make_agree_with_number(
            abs(int(_weather[index]['feels_like']))).word
        if len(_weather[index]['date'].split('-')) != 1:
            date = _weather[index]['date'].split('-')[-1] + '.' + _weather[index]['date'].split('-')[-2]
        else:
            date = _weather[index]['date']
        osh = _weather[index]['condition']

        mes = "Погода на {}.\nТемпература {} (ощущается как {}), {}".format(date, degrise, degrise1, osh)

        bot.edit_message_text(text=mes,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id, parse_mode='markdown',
                              reply_markup=_key_board)

    elif query.data == '3':
        weather[query.message.message_id][1] -= 1
        _key_board = inline_keyboard_2
        if weather[query.message.message_id][1] <= 0:
            weather[query.message.message_id][1] = 0
            _key_board = inline_keyboard_1

        _weather = weather[query.message.message_id][0]
        index = weather[query.message.message_id][1]
        gr = morph.parse('градус')[0]
        degrise = str(_weather[index]['temp']) + ' ' + gr.make_agree_with_number(abs(int(_weather[index]['temp']))).word
        degrise1 = str(_weather[index]['feels_like']) + ' ' + gr.make_agree_with_number(
            abs(int(_weather[index]['feels_like']))).word
        if len(_weather[index]['date'].split('-')) != 1:
            date = _weather[index]['date'].split('-')[-1] + '.' + _weather[index]['date'].split('-')[-2]
        else:
            date = _weather[index]['date']
        osh = _weather[index]['condition']

        mes = "Погода на {}.\nТемпература {}(ощущается как {}), {}".format(date, degrise, degrise1, osh)

        bot.edit_message_text(text=mes,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id, parse_mode='markdown',
                              reply_markup=_key_board)

    return 2


def traffic_congestion(bot, update, args):
    if args!=[]:
        if [True for j in args if ':' in j]:
            address = (''.join(args)).split(':')
            address1, address2 = address[0], address[1]
            try:
                lat, lon = get_coordinates(address2)
                ll, spn = get_ll_span(address1, [str(lat) + ',' + str(lon)], [address2])
            except:
                update.message.reply_text("Извини, но я не смог найти этот адрес :(")

        elif len(args)>=1:
            address1 = args
            try:
                ll, spn = get_ll_span(address1, [], [])
            except:
                update.message.reply_text("Извини, но я не смог найти этот адрес :(")

        static_api_request = "http://static-maps.yandex.ru/1.x/?ll={}&l=map,trf&spn={}".format(ll, spn)
        bot.sendPhoto(
            update.message.chat.id,
            static_api_request
        )

    else:
        update.message.reply_text("Нет адреса")


def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('guide', guide)],

        states={
            1: [MessageHandler(Filters.text, town, pass_user_data=True)],
            2: [MessageHandler(Filters.text, interests, pass_user_data=True),
                CallbackQueryHandler(change_places)],
        },

        fallbacks=[CommandHandler('stop', stop)]
    )

    dp.add_handler(conv_handler)

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('traffic_congestion', traffic_congestion, pass_args=True))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()