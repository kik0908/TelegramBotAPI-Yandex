from random import choice, shuffle
from itertools import cycle

from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from geocoder import  search
from settings import TOKEN


places = {'спорт': ['стадион', 'дворец спорта', 'тренажёрный зал', 'бассейн'],
          'культура':['театр','музей', 'библиотека', 'дом культуры'],
          'развлечения':['клуб', 'кино', 'сауна', 'бар', 'караоке','квесты', 'боулинг', 'бильярдный зал', 'спортивно-тактические клубы'],
          'медицина':['больница', 'поликлиника', 'стоматология', 'травмпункт'],
          'медтовары':['аптека', 'медтовары'],
          'животные':['Товары для животных', 'ветеленарная клиника'],
          'питание':['кафе', 'ресторан', 'макдональдс', 'kfc', 'столовая', 'пиццерия', 'суши бар', 'банкетный зал'],
          'религия':['православный храм','мечеть', 'собор'],
          'магазины':['торговый центр', 'спорттовары', 'магазин одежды', 'детский магазин', 'канцтовары', 'книжный магазин'],
          'автосервис':['штрафстоянка','шиномонтаж','заправка','автомойка', 'авторемонт', 'стоянка', 'автохимия','шины, диски'],
          'туризм':['гостиница','хостел','отель','база отдыха','авиабилеты','железнодорожные билеты'],
          'прогулка':['парк','сквер','экскурсии','достопримечательность','отдых'],
          }

reply_keyboard = [['Развлечения', 'Питание'],
                  ['Спорт', 'Религия', 'Туризм'],
                  ['Культура', 'Магазины'],
                  ['Автосервис', 'Медтовары', 'Медицина'],
                  ['Животные','Прогулка'],
                  ['Сменить город']]

keyboard_yes_or_no = [['Да','Нет']]

inline_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Следующее место', callback_data=1)]])

nazvanie_potom = {}

def start(bot, update):
    update.message.reply_text("Привет! :)\n"
                              "Я твой бот-помощник!\n")
    update.message.reply_text("Я помогу тебе найти интересные места в городе на основе твоих интересов.\n"
                              "Для этого напиши /guide\n")
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
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Выберите сферу которая вас интересует", reply_markup=markup)
    return 2

def stop(bot, update):
    update.message.reply_text("Удачи!")
    return ConversationHandler.END

def interests(bot, update, user_data):
    global nazvanie_potom

    message = update.message.text.lower()
    if message == 'сменить город':
        return 1
    elif message in places:
        update.message.reply_text("Начинаю поиск...")

        _1 = 8#choice(range(3, len(places[message]+1)))

        datas = []
        _a = []

        print('zashel 2')

        _places = []
        random_places = []

        for _ in range(len(places[message]), 0, -1):
            random_place = choice(places[message])
            while True:
                if random_place not in random_places:
                    break
                random_place = choice(places[message])

            result = search(user_data['locality'], random_place, _1)
            print('Результат поиска: ',result)
            print(1)
            for _ in result:
                data = _[0]
                coord = _[1]

                if data not in datas:
                    static_api_request = "http://static-maps.yandex.ru/1.x/?ll={}&l=map&z=15&pt={},pm2blywm1".format(coord, coord)
                    print('Информация прошла проверку: ', data)
                    _a.append('[Картинка.]({})\n{} ({})'.format(static_api_request, data, random_place))
                    datas.append(data)
                    

        print(_places)

        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        shuffle(_a)

        print('proshel 2 chikl')
        print(_a)
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


def traffic_congestion(bot, update, args):
    if [True for j in args if ':' in j]:
        address = (''.join(args)).split(':')
        address1, address2 = address[0], address[1]
        try:
            lat, lon = get_coordinates(address2)
            print(get_coordinates(address1), lat, lon)
            ll, spn = get_ll_span(address1, [str(lat)+','+str(lon)], [address2])
            print(ll, spn)
        except:
            update.message.reply_text("Извини, но я не смог найти этот адрес :(")
    else:
        address1 = args
        ll, spn = get_ll_span(address1, [])
    static_api_request = "http://static-maps.yandex.ru/1.x/?ll={}&l=map,trf&spn={}".format(ll,spn)
    bot.sendPhoto(
        update.message.chat.id,
        static_api_request
    )

def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))

    conv_handler = ConversationHandler(
        # Без изменений
        entry_points=[CommandHandler('guide', guide)],
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_user_data=True)],

        states={
            1: [MessageHandler(Filters.text, town, pass_user_data=True)],
            2: [MessageHandler(Filters.text, interests, pass_user_data=True),
                CallbackQueryHandler(change_places, pass_user_data=True)],
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