from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from geocoder import get_coordinates, poisk, get_ll_span
from mapapi import show_map

def start(bot, update):
    update.message.reply_text(
        "Привет! :)\n"
        "Я бот, который может тебе найти интересные места города на основе твоих интересов.\n"
        "Какой город тебя интересует?")
    return 1

def town(bot, update, user_data):
    user_data['locality'] = update.message.text
    update.message.reply_text("А теперь расскажи немного о себе :)")
    return 2

def interests(bot, update, user_data):
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

def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        # Без изменений
        entry_points=[CommandHandler('start', start)],

        states={
            1: [MessageHandler(Filters.text, town, pass_user_data=True)],
            2: [MessageHandler(Filters.text, interests, pass_user_data=True)]
        },

        fallbacks=[CommandHandler('stop', stop)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(MessageHandler(Filters.text, back))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()