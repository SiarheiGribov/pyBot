# -*- coding: utf-8 -*-

import re
import time
from urllib.error import HTTPError

import requests
from bs4 import BeautifulSoup

import login

# -------------------------------------------------
limit = 5000  # Количество досматриваемых правок. Для анонимов и участников: от 1 до 500; Для ботов: от 1 до 5000.
# Бот проверяет правки от нынешнего момента до времени последней проходки. Однако максимальное число проверяемых правок
# можно регулировать этим параметром.
days_history = 14  # количество дней, по истечению которых бот удалит неактуальный уведомляющий шаблон из отчёта


# -------------------------------------------------


# функция проверки и выгрузки отчёта
def check(wl_c, title, diff_text, revid, oldid, user):
    diff_text = diff_text.replace("]]", "")
    s = 0
    reason = ""
    end = ['ка', 'ша', 'шей', 'иня', 'иней', 'ня', 'яка', 'ица', 'ицей', 'иха', 'чка', 'ичка', 'есса', 'эсса', "антка",
           "антша"]
    case_end = ['', 'а', 'е', 'и', 'ы', 'у', 'ю', 'я', 'ам', 'ям', 'ей', 'ов', 'ев', 'ой', 'ою', 'ею', 'ом', 'ем',
                'ами', 'ями', 'ах', 'ях']
    pub = []
    while s <= 15:
        reg = re.findall(r'\b(\w*' + end[s][:-1] + r')\w\b', diff_text, flags=re.U | re.I)
        n = -1
        # если на новой странице есть слова на заданное окончание (феминитивное без последней буквы)
        while n < len(reg) - 1:
            n += 1
            word = reg[n].lower()
            # ищем базовое слово (в именительном падеже мужского рода)
            reg_base = re.findall(r'\b(\w*?)' + end[s][:-1] + r'\b', word, flags=re.U | re.I)
            if len(reg_base) > 0:
                if reg_base[0] != "":
                    check_wl = reg_base[0]
                    # если в слове есть е/ё, добавляем в паттерн вариабельность
                    if "е" in reg_base[0] or "ё" in reg_base[0]:
                        check_wl = re.sub(r'[е|ё]', u'[е|ё]', reg_base[0])
                    check_wl_reg = re.findall(r'\b(' + check_wl + r')\b', wl_c, flags=re.U | re.I)
                    if len(check_wl_reg) == 0:  # проверка на отсутствие слова в именительном падеже в белом списке
                        reglist_p = re.findall(r'\b(' + check_wl + r')\b', listP, flags=re.U | re.I)
                        # проверка на присутствие слова в именительном падеже в списке «словоформ»
                        if len(reglist_p) > 0:
                            m = 0
                            while m <= 21:  # ищем эти слова в падежных окончаниях по тексту
                                reg2 = re.findall(
                                    r'\b(' + check_wl + end[s][:-1] + case_end[m] + r')\b', diff_text,
                                    flags=re.U | re.I)
                                if len(reg2) > 0:
                                    j = 0
                                    while j <= len(reg2) - 1:
                                        check_wl2 = reg2[j].lower()
                                        # если в слове есть е/ё, добавляем в паттерн вариабельность
                                        if "е" in check_wl2 or "ё" in check_wl2:
                                            check_wl2 = re.sub(r'[е|ё]', u'[е|ё]', check_wl2)
                                        check_wl_reg2 = re.findall(r'\b(' + check_wl2 + r')\b', wl2, flags=re.U | re.I)
                                        # проверка на отсутствие конечного найденного слова во втором белом списке
                                        if len(check_wl_reg2) == 0:
                                            if reason == "":
                                                reason = reg2[j].lower()
                                            else:
                                                if reg2[j].lower() not in reason:
                                                    reason += ", " + reg2[j].lower()
                                        j += 1
                                m += 1
        s += 1
    for bl_line in bl:  # проверка на наличие слова в чёрном списке
        word4 = bl_line.strip('\r\n')
        # если в слове есть е/ё, добавляем в паттерн вариабельность
        if "е" in bl_line.strip('\r\n') or "ё" in bl_line.strip('\r\n'):
            word4 = re.sub(r'[е|ё]', u'[е|ё]', bl_line.strip('\r\n'))
        reg_bl = re.findall(r'\b(' + word4 + r')\b', diff_text, flags=re.U | re.I)
        if len(reg_bl) > 0:
            if reason == "":
                reason = bl_line.strip('\r\n').lower()
            else:
                if bl_line.strip('\r\n').lower() not in reason:
                    reason += ", " + bl_line.strip('\r\n').lower()

    if reason != "":  # вывод: если есть подозрительные слова
        pre_pub = "{{User:IluvatarBot/Подозрительная правка|" + str(title) + "|" + str(oldid) + "|" + str(
            revid) + "|" + str(reason) + "|" + str(user) + "|" + str(int(time.time())) + "}}"

        # print(pre_pub)
        pub.append(pre_pub)
    if len(pub) > 0:
        w = 0
        pub_complete = ""
        while w <= len(pub) - 1:
            pub_complete += pub[w] + "\n"
            w += 1
        return pub_complete
        # конец функции проверки и выгрузки отчёта


# Запрашиваем все списки (список профессий, белый список (сущ. в имен. падеже), конечный белый список, чёрный список),
# файл с последним таймстампом, id последней проверенной ревизии
timest = ""
timeid = ""
wl = ""
try:
    URL_BL = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Феминитивы/Badlist'
    bl = requests.get(URL_BL).text.rsplit("\n")
    URL_WL = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Феминитивы/Whitelist'
    wl = requests.get(URL_WL).text
    URL_WL2 = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Феминитивы/Whitelist2'
    wl2 = requests.get(URL_WL2).text
    with open('pyBot/wikipedia/service/list_of_works.txt', encoding="utf-8") as f:
        listP = f.read()
        f.close()
    with open('pyBot/wikipedia/service/time.txt', encoding="utf-8") as lines:
        line = lines.read().splitlines()
        lines.close()
    timest = line[0]
    timeid = line[1]
except HTTPError:
    print("http error during donwloading lists")
    exit()

token, cookies = login.login()  # логинимся
json_parsed = {}
try:  # Запрашиваем список новых правок
    payload = {'action': 'query', 'format': 'json', 'list': 'recentchanges', 'rcnamespace': '0|6|10|12|14',
               'rcprop': 'title|ids|user|timestamp', 'rcshow': '!redirect|!bot', 'rcend': timest, 'rctype': 'new|edit',
               'rclimit': limit,
               'token': token}
    json_parsed = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies).json()
except requests.exceptions.RequestException as e:
    print("http error during get list of edits")
    print(e)
    exit()
i = -1
pb = ""
pb2 = ""
URL1 = "None"
diff_parsed0 = ""
while i < len(json_parsed['query']['recentchanges']) - 1:
    i += 1
    try:
        if i == 0:
            timest = json_parsed['query']['recentchanges'][i]['timestamp']
            timeid = json_parsed['query']['recentchanges'][i]['revid']
        if not json_parsed['query']['recentchanges'][i]['revid'] == timeid:
            if str(json_parsed['query']['recentchanges'][i]['old_revid']) == "0":  # если это новая страница
                URL1 = "https://ru.wikipedia.org/w/?action=raw&utf8=1&title=" + \
                       json_parsed['query']['recentchanges'][i]['title']
                pb = check(wl, json_parsed['query']['recentchanges'][i]['title'], requests.get(URL1).text,
                           str(json_parsed['query']['recentchanges'][i]['revid']), 0,
                           str(json_parsed['query']['recentchanges'][i]['user']))
            else:  # если это правка на существующей странице
                URL1 = "https://ru.wikipedia.org/w/api.php?action=compare&format=json&prop=diff&utf8=1&fromrev=" + str(
                    json_parsed['query']['recentchanges'][i]['old_revid']) + "&torev=" + str(
                    json_parsed['query']['recentchanges'][i]['revid'])
                diff = ""
                diff_parsed = requests.post(URL1).json()
                if "error" not in diff_parsed:
                    for chengeDiff in BeautifulSoup(diff_parsed['compare']['*'], features="html.parser").findAll("ins",
                            {"class": "diffchange diffchange-inline"}):  # Вытаскиваем из диффа изменённые слова
                        diff += str(chengeDiff) + "\n"
                    # Вытаскиваем из диффа новые строки
                    for diffAdd in BeautifulSoup(diff_parsed['compare']['*'], features="html.parser").findAll("tr"):
                        if "diffchange diffchange-inline" not in str(diffAdd) and "diff-deletedline" not in str(
                                diffAdd):
                            for diffAdd2 in BeautifulSoup(str(diffAdd), features="html.parser").findAll("td", {
                                    "class": "diff-addedline"}):
                                diff += str(diffAdd2) + "\n"
                    if "user" not in json_parsed["query"]["recentchanges"][i] and "userhidden" in \
                            json_parsed["query"]["recentchanges"][i]:
                        username = "HIDDEN"
                    else:
                        username = str(json_parsed['query']['recentchanges'][i]['user'])
                    pb = check(wl, json_parsed['query']['recentchanges'][i]['title'], diff,
                               str(json_parsed['query']['recentchanges'][i]['revid']),
                               str(json_parsed['query']['recentchanges'][i]['old_revid']),
                               username)

            if pb:
                pb2 += pb

    except HTTPError as he:  # удалённые и переименованные без перенаправления страницы
        print("http error during main loop: " + str(he) + ". (" + URL1 + ")")
    except requests.exceptions.RequestException as rex:  # удалённые и переименованные без перенаправления страницы
        print("Request error during main loop: " + str(rex) + ". (" + URL1 + ")")
    except ValueError as ve:  # Неудачные запросы (лаг сервера и тп). В общем случае: битый JSON
        print("JSON error during main loop: " + str(ve) + ". (" + URL1 + ")" + " [" + str(diff_parsed0) + "]")
    except BaseException as be:  # ошибка парсинга
        print("HTMLParse error during main loop: " + str(be) + ". (" + URL1 + ")")
    except KeyError as ke:  # скрытые версии
        print("KeyError (bt) error during main loop: " + str(ke) + ". (" + URL1 + ")")

report_page = []
if pb2 != "":  # Если переменная с результатам не пуста, публикуем. Предварительно выпиливая уведомления,
    # размещённые более указанного кол-ва дней назад
    time.sleep(1)
    report_page_url = "https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Феминитивы/Отчёт"
    try:
        report_page = requests.get(report_page_url).text.rsplit("\n")
    except HTTPError as e:
        print("Error during get report_page (" + str(e) + ").")
        exit()
    new_pub = []
    for line2 in report_page:  # удаляем устаревшие шаблоны
        timeReg = re.findall(r"(\d*)?}}", line2.strip('\r\n'), re.U | re.I)
        if not len(timeReg) > 0:
            print("Timestamp error (один из шаблонов на странице не имеет отметки времени)")
            exit()
        timePast = int(time.time()) - int(timeReg[0])
        hoursPast = int(days_history) * 24 * 60 * 60
        if not timePast >= int(hoursPast):
            new_pub.append(line2 + "\n")
        report_page = ''.join(new_pub)
    report_page = pb2 + report_page
    payload = {'action': 'edit', 'format': 'json', 'title': 'User:IluvatarBot/Феминитивы/Отчёт', 'utf8': '',
               'text': report_page,
               'summary': 'Выгрузка отчёта', 'token': token}
    time.sleep(1)
    try:
        reqF = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
    except requests.exceptions.RequestException as e:
        print("Error during get publishing (" + str(e) + ").")
        exit()
    # print pb2

if not str(timest) == "" and not str(timeid) == "":
    time_file = open("pyBot/wikipedia/service/time.txt", "w")
    time_file.write(str(timest).replace("Z", ".000Z") + "\n" + str(timeid))
    time_file.close()
    try:  # совершаем нулевую правку
        null_edit_page = requests.get(
            'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Феминитивы').text
        payload = {'action': 'edit', 'format': 'json', 'title': 'User:IluvatarBot/Феминитивы', 'utf8': '',
                   'text': null_edit_page, 'summary': 'null edit', 'token': token}
        nullReq = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
    except HTTPError:
        print("http error during doing null edit")
        exit()
    # print "Отчёт выгружен"
