from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from geocoder import get_coordinates, poisk, get_ll_span, search
from mapapi import show_map
from settings import TOKEN
from random import choice


places = {'спорт': ['стадион', 'дворец спорта', 'тренажёрный зал', 'бассейн'],
          'культура':['театр','музей', 'библиотека'],
          'развлечения':['клуб', 'кино', 'сауна', 'бар'],
          'медицина':['аптека', 'больница', 'поликлиника', 'стоматология'],
          'питание':['кафе', 'ресторан', 'макдональдс', 'kfc'],
          'религия':['православный храм','мечеть'],
          'магазины':['супермаркет', 'спорттовары', 'магазин одежды']
          }

def start(bot, update, user_data):
    update.message.reply_text(
        "Привет! :)\n"
        "Я бот, который может тебе найти интересные места города на основе твоих интересов.\n")
    update.message.reply_text("Какой город тебя интересует?")
    return 1

def town(bot, update, user_data):
    user_data['locality'] = update.message.text
    _ans = search(user_data["locality"], 'кафе')
    if not _ans:
        print('Ошибка при поиске города')
        update.message.reply_text("Прости, но я не смог найти такой город.\nКакой город тебя интересует?")
        return 1
    reply_keyboard = [['Развлечения', 'Питание'],
                      ['Спорт','Религия','Медицина'],
                      ['Культура', 'Магазины'],
                      ['Сменить город']]

    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Выберите сферу которая вас интересует", reply_markup=markup)
    return 2

def town2(bot, update):
    reply_keyboard = [['Развлечения', 'Питание'],
                      ['Спорт','Религия','Медицина'],
                      ['Культура', 'Магазины']]

    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Выберите сферу которая вас интересует", reply_markup=markup)
    return 2

def interests_(bot, update, user_data):
    user_data['hobby'] = update.message.text.split() # пример: пользователь ввёл 'музей кино театр'
    update.message.reply_text("Отлично! Пойду искать!")

    coordinate_x, coordinate_y = get_coordinates(user_data['locality'])
    toponym_point = "{0},{1}".format(coordinate_x, coordinate_y)

    coordinates, time = [], []
    for hobby in user_data['hobby']:
        ll_place, marker = poisk(toponym_point, hobby)
        coordinates.append(ll_place)
        time.append(marker)

    ll, spn = get_ll_span(toponym_point, coordinates)
    ll_spn = "ll={ll}&spn={spn}".format(**locals())
    point_param='pt='
    for j in range(len(coordinates)):
        if j==0:
            point_param+='{},{}'.format(coordinates[j], time[j])
        else:
            point_param += '~{},{}'.format(coordinates[j], time[j])

    show_map(ll_spn, "map", add_params=point_param)
    static_api_request = "http://static-maps.yandex.ru/1.x/?{}&l=map&{}".format(ll_spn, point_param)
    # print(static_api_request)
    bot.sendPhoto(
        update.message.chat.id,
        static_api_request
    )
    return ConversationHandler.END

def stop(bot, update):
    update.message.reply_text("Эх...")
    return ConversationHandler.END

def back(bot, update):
    update.message.reply_text(update.message.text)

def interests(bot, update, user_data):
    message = update.message.text.lower()
    if message == 'сменить город':
        return 1
    elif message in places:
        _1 = 3#choice(range(3, len(places[message]+1)))
        print('zashel2')
        _places = []
        for _ in range(_1, 0, -1):
            _places.append(search(user_data['locality'], choice(places[message]), _))
        print(_places)
        _a = []
        reply_keyboard = [['Развлечения', 'Питание'],
                          ['Спорт', 'Религия', 'Медицина'],
                          ['Культура', 'Магазины'],
                          ['Сменить город']]

        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        for _ in _places:
            for data, coord in _:
                print(2)
                if data not in _a:
                    static_api_request = "http://static-maps.yandex.ru/1.x/?ll={}&l=map&z=15&pt={},pm2blywm1".format(coord, coord)
                    print(3)
                    #bot.sendPhoto(
                    #    update.message.chat.id,
                    #    static_api_request
                    #)
                    update.message.reply_text(static_api_request+'\n'+data)#data)
                    _a.append(data)

        print('proshel 2 chikl')
        update.message.reply_text('Информация выдана', reply_markup=markup)
        return 2
    else:
        return 2


def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        # Без изменений
        entry_points=[CommandHandler('start', start, pass_user_data=True)],

        states={
            1: [MessageHandler(Filters.text, town, pass_user_data=True)],
            2: [MessageHandler(Filters.text, interests, pass_user_data=True)],
            3: [MessageHandler(Filters.text, town2 )]
        },

        fallbacks=[CommandHandler('stop', stop)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(MessageHandler(Filters.text, back))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()