import csv
import re
import requests
from bs4 import BeautifulSoup


def check_text(message):
    text = message.text
    flag = True
    if ' ' in text:
        fail_message = 'Напишите только 1 слово'
        flag = False
    elif re.search(r'[^a-zA-Zа]', text):
        fail_message = 'Используйте только английские буквы'
        flag = False
    elif len(text) == 1:
        fail_message = 'Минимум 2 буквы'
        flag = False
    else:
        try:
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
            }

            url = f'https://dictionary.cambridge.org/us/dictionary/english/{text}'

            html = requests.get(url, headers=headers)
            soup = BeautifulSoup(html.text, features='html.parser')

            final_keyword = soup.find('span', class_='hw dhw')  # Получаем слово в простой форме
            final_keyword_string = final_keyword.string
            fail_message = 'Ошибок нет'

        except AttributeError:
            fail_message = 'Такого слова нет'
            flag = False

    return flag, fail_message


def get_data_from_cambridge(word_data, message):
    ''' Получаем данные о слове на Cambridge Dictionary:
    – Слово в простой форме
    – Произношение в .mp3 '''

    keyword = message.text.lower()

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }

    url = f'https://dictionary.cambridge.org/us/dictionary/english/{keyword}'

    html = requests.get(url, headers=headers)
    soup = BeautifulSoup(html.text, features='html.parser')

    refined_keyword = soup.find('span', class_='hw dhw')  # Получаем слово в простой форме
    keyword = refined_keyword.string

    search = soup.find_all(attrs={"type": "audio/mpeg"}, limit=1)  # Скачиваем звук
    url_sound = 'https://dictionary.cambridge.org/' + str(search).replace('[<source src="/', '').replace('" type="audio/mpeg"/>]', '')

    response = requests.get(url_sound, headers=headers)
    with open(f'sounds/{keyword}.mp3', 'wb') as mp3:
        mp3.write(response.content)

    word_data.update({
        'en': keyword,
    })

    return word_data, keyword


def get_data_from_promt(word_data, keyword):
    ''' Получаем данные о слове на Cambridge Dictionary:
    – Перевод на ру
    – Транскрипция произношения
    – Часть речи
    – Спрежение
    – Пример фраз на англ
    – Перевод фраз ан ру '''

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }

    url = f'https://www.translate.ru/%D0%BF%D0%B5%D1%80%D0%B5%D0%B2%D0%BE%D0%B4/%D0%B0%D0%BD%D0%B3%D0%BB%D0%B8%D0%B9%D1%81%D0%BA%D0%B8%D0%B9-%D1%80%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9/{keyword}'

    html = requests.get(url, headers=headers)
    soup = BeautifulSoup(html.text, features='html.parser')

    translate = soup.find_all('span', class_='result_only sayWord', limit=2)  # Получаем русские слова
    words_list = []
    for word in translate:
        words_list.append(word.string)
    ru_words = ', '.join(words_list)

    try:
        part_of_speech = soup.find('span', class_='ref_psp')  # Получаем часть речи
        part_of_speech_string = part_of_speech.string
    except:
        part_of_speech_string = ''

    try:
        other_forms = soup.find('div', class_='otherImportantForms')  # Получаем спряжения
        other_forms_string = other_forms.string.strip()
    except:
        other_forms_string = ''

    en_phrases_list = []
    phrases_en = soup.find_all('div', class_='samSource', limit=2)  # Получаем английские фразы
    for phrase in phrases_en:
        a = str(phrase)
        a = a.replace('<div class="samSource"><span style="color:#14426f">', '').replace(' class="sourceSampleSearch"', "").replace('.</span></div>', '').replace('span', 'b').replace('</div>', '')
        en_phrases_list.append(a)

    ru_phrases_list = []
    phrases_ru = soup.find_all('div', class_='samTranslation', limit=2)  # Получаем русские фразы
    for phrase in phrases_ru:
        a = str(phrase)
        a = a.replace('<div class="samTranslation"><span>', '').replace(' class="sourceSampleSearch"', '').replace('.</span></div>', '').replace('</div>', '').replace('span', 'b')
        ru_phrases_list.append(a)

    phrases = ''
    for i in range(len(en_phrases_list)):
        phrases += en_phrases_list[i] + '<br>' + ru_phrases_list[i] + '<br><br>'
    phrases = phrases[:-8]

    word_data.update({
        'ru': ru_words,
        'phrases': phrases,
        'other_forms': other_forms_string,
        'part_of_speech': part_of_speech_string,
        'sounds': f'[sound:{keyword}.mp3]',
    })
    return word_data, keyword


def update_csv(word_data, message):
    csvfile = open(f'docs/{message.from_user.id}.csv', 'a', encoding='utf-8')
    c = csv.writer(csvfile)
    c.writerow(word_data.values())
    csvfile.close()


def main(message):
    while True:
        word_data = {}
        word_data, keyword = get_data_from_cambridge(word_data, message)
        word_data, keyword = get_data_from_promt(word_data, keyword)
        update_csv(word_data, message)
        return word_data
