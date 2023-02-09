import os
import csv
from zipfile import ZipFile
from auth_token import TOKEN
from entoankibot import main, check_text
from telebot import types, TeleBot

bot = TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn = typЫes.KeyboardButton('/csv')
    markup.add(btn)
    bot.send_message(message.chat.id, 'Шаг 1. – Отправляй слова для сбора данных\n'
                                      'Шаг 2. – Пиши /csv – для выгрузки в Anki', reply_markup=markup)


@bot.message_handler(commands=['csv'])
def scv(message):
    try:
        file = open(f'docs/{message.from_user.id}.csv', 'rb')
        bot.send_document(message.chat.id, file)
        with open(f'docs/{message.from_user.id}.csv') as f:
            reader = csv.reader(f)
            words_list = []
            for column in reader:
                words_list.append(column[0])
        with ZipFile(f"{message.from_user.id}.zip", "a") as myzip:
            for word in words_list:
                myzip.write(f"sounds/{word}.mp3")
        file_zip = open(f"{message.from_user.id}.zip", 'rb')
        bot.send_document(message.chat.id, file_zip)
        os.remove(f'docs/{message.from_user.id}.csv')
        os.remove(f"{message.from_user.id}.zip")

    except FileNotFoundError:
        bot.send_message(message.chat.id, 'Нет слов для выгрузки', parse_mode='html')


@bot.message_handler()
def get_user_text(message):
    flag, fail_message = check_text(message)
    if flag is True:
        word_data = main(message)
        file = open(f'sounds/{word_data.get("en")}.mp3', 'rb')
        if word_data.get("other_forms") == '':
            bot.send_audio(message.chat.id, file, f'Англ: <b>{word_data.get("en")}</b>\n'
                                                  f'Рус: <b>{word_data.get("ru")}</b>',  parse_mode='html')
        else:
            bot.send_audio(message.chat.id, file, f'Англ: <b>{word_data.get("en")}</b>\n'
                                                  f'Рус: <b>{word_data.get("ru")}</b>\n'
                                                  f'Спряжения: <i>{word_data.get("other_forms")}</i>', parse_mode='html'
                           )
    else:
        bot.send_message(message.chat.id, fail_message, parse_mode='html')


if __name__ == "__main__":
    bot.polling(none_stop=True)
