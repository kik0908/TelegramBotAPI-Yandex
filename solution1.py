from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from geocoder import get_coordinates, poisk, get_ll_span, search
from mapapi import show_map
from settings import TOKEN
from random import choice
from itertools import cycle


places = {'спорт': ['стадион', 'дворец спорта', 'тренажёрный зал', 'бассейн'],
          'культура':['театр','музей', 'библиотека'],
          'развлечения':['клуб', 'кино', 'сауна', 'бар'],
          'медицина':['аптека', 'больница', 'поликлиника', 'стоматология'],
          'питание':['кафе', 'ресторан', 'макдональдс', 'kfc'],
          'религия':['православный храм','мечеть'],
          'магазины':['супермаркет', 'спорттовары', 'магазин одежды']
          }

reply_keyboard = [['Развлечения', 'Питание'],
                  ['Спорт', 'Религия', 'Медицина'],
                  ['Культура', 'Магазины'],
                  ['Сменить город']]

inline_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Следующее место', callback_data=1)]])

nazvanie_potom = {}

def start(bot, update, user_data):
    update.message.reply_text(
        "Привет! :)\n"
        "Я бот, который может тебе найти интересные места города на основе твоих интересов.\n")
    update.message.reply_text("Если захочешь узнать про пробки в городе, то набери\n",
                              "/traffic_congestion {ПУНКТ_ОТПРАВЛЕНИЯ}:{ПУНКТ_НАЗНАЧЕНИЯ}\n",
                              "или\n",
                              "/traffic_congestion {АДРЕС}\n")
    update.message.reply_text("Какой город тебя интересует?")
    return 1

def town(bot, update, user_data):
    user_data['locality'] = update.message.text
    _ans = search(user_data["locality"], 'кино')
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

def stop(bot, update):
    update.message.reply_text("Удачи!")
    return ConversationHandler.END

def traffic_congestion(bot, update, args):
    if ':' in args:
        address1, address2 = args.split(':')
        coord1, coord2 = get_coordinates(address1), get_coordinates(address2)
        print(coord1, coord2)
    else:
        address1 = args

def back(bot, update):
    update.message.reply_text(update.message.text)

def interests(bot, update, user_data):
    global nazvanie_potom

    message = update.message.text.lower()
    if message == 'сменить город':
        return 1
    elif message in places:
        _1 = 10#choice(range(3, len(places[message]+1)))
        print('zashel 2')
        _places = []
        for _ in range(_1, 0, -1):
            _places.append(search(user_data['locality'], choice(places[message]), _))
        print(_places)
        datas = []

        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

        _a = []

        for _ in _places:
            for data, coord in _:
                print(2)
                if data not in datas:
                    static_api_request = "http://static-maps.yandex.ru/1.x/?ll={}&l=map&z=15&pt={},pm2blywm1".format(coord, coord)
                    print(3)
                    #bot.sendPhoto(
                    #    update.message.chat.id,
                    #    static_api_request
                    #)
                    #update.message.reply_text('[Картинка.]({})\n{}'.format(static_api_request, data), parse_mode='markdown')#data)
                    _a.append('[Картинка.]({})\n{}'.format(static_api_request, data))
                    datas.append(data)

        print('proshel 2 chikl')
        _a = cycle(_a)
        _1 = update.message.reply_text(next(_a), reply_markup=inline_keyboard)
        nazvanie_potom[_1.message_id] = _a
        update.message.reply_text("Выберите сферу которая вас интересует", reply_markup=markup)

        return 2
    else:
        return 2

def change_places(bot, update, user_data):
    global nazvanie_potom

    query = update.callback_query
    if query.data == '1':
        bot.edit_message_text(text=next(nazvanie_potom[query.message.message_id]),
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id, parse_mode='markdown',
                              reply_markup=inline_keyboard)
    return 2



def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        # Без изменений
        entry_points=[CommandHandler('start', start, pass_user_data=True)],

        states={
            1: [MessageHandler(Filters.text, town, pass_user_data=True)],
            2: [MessageHandler(Filters.text, interests, pass_user_data=True),
                CallbackQueryHandler(change_places, pass_user_data=True)]
        },

        fallbacks=[CommandHandler('stop', stop)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(MessageHandler(Filters.text, back))
    dp.add_handler(CommandHandler('traffic_congestion', traffic_congestion, pass_args=True))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()