# -*- coding: utf-8 -*-

import sys
import requests
import urllib2
import json
import re
import os
import time
import login
import ConfigParser
from BeautifulSoup import BeautifulSoup
from HTMLParser import HTMLParseError
reload(sys)
sys.setdefaultencoding('utf8')

#Copyright (c) 2017 Siarhei Gribov, [[User:Iluvatar]]
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
# -------------------------------------------------
limit = 5000 # количество досматриваемых правок. Для анонимов и участников: от 1 до 500; Для ботов: от 1 до 5000. Бот проверяет правки от нынешнего момента
# до времени последней проходки. Однако максимальное число проверяемых правок можно регулировать этим параметром.
days_history = 14 # количество дней, по истечению которых бот удалит уведомляющий шаблон из отчёта как утративший актуальность
# -------------------------------------------------


config = ConfigParser.RawConfigParser()
config.read(os.path.abspath(os.path.dirname(__file__)) + '/bottoken.ini')
bottoken = (config.get('Token', 'bottoken'))

# функция проверки и выгрузки отчёта
def check(wl, title, URL, diff_text, revid, oldid, user):
    s = 0
    reason = ""
    end = ['ка', 'ша', 'шей', 'иня', 'иней', 'ня', 'яка', 'ица', 'ицей', 'иха', 'чка', 'ичка', 'есса', 'эсса']
    case_end = ['', 'а', 'е', 'и', 'ы', 'у', 'ю', 'я', 'ам', 'ям', 'ей', 'ов', 'ев', 'ой', 'ою', 'ею', 'ом', 'ем', 'ами', 'ями', 'ах', 'ях']
    pub = []
    while s<=13:
        reg = re.findall(ur'\b(\w*' + unicode(end[s])[:-1] + ur')\w\b', unicode(diff_text), flags=re.U|re.I)
        n = -1
        while n < len(reg) - 1:  # если в новой странице есть слова на заданное окончание (феминитивное окончание без последней буквы)
            n += 1
            word = reg[n].lower()
            regBase = re.findall(ur'\b(\w*?)' + unicode(end[s])[:-1] + ur'\b', unicode(word), flags=re.U|re.I) # ищем базовое слово (в именительном падаже мужского рода
            if len(regBase) > 0:
                if regBase[0] <> "":
                    checkWL = regBase[0]
                    if (unicode("е") in unicode(regBase[0])) or (unicode("ё") in unicode(regBase[0])):  # если в слове есть е/ё, добавляем в паттерн вариабельность
                        checkWL = re.sub(ur'[е|ё]', u'[е|ё]', unicode(regBase[0]))
                    checkWLReg = re.findall(ur'\b(' + checkWL + ur')\b', unicode(wl), flags=re.U | re.I)
                    if len(checkWLReg) == 0:  # проверка на отсутствие слова в именительном падеже в белом списке
                        reglistP = re.findall(ur'\b(' + checkWL + ur')\b', unicode(listP), flags=re.U | re.I)
                        if len(reglistP) > 0: # проверка на присутствие слова в именительном падеже в списке «словоформ»
                            m = 0
                            while m <= 21:  # ищем эти слова в падежных окончаниях по тексту
                                reg2 = re.findall(ur'\b(' + checkWL + unicode(end[s])[:-1] + unicode(case_end[m]) + ur')\b', unicode(diff_text),
                                                  flags=re.U | re.I)
                                if len(reg2) > 0:
                                    j = 0
                                    while j <= len(reg2) - 1:
                                        checkWL2 = reg2[j].lower()
                                        if (unicode("е") in unicode(checkWL2)) or (unicode("ё") in unicode(checkWL2)):  # если в слове есть е/ё, добавляем в паттерн вариабельность
                                            checkWL2 = re.sub(ur'[е|ё]', u'[е|ё]', unicode(checkWL2))
                                        checkWLReg2 = re.findall(ur'\b(' + checkWL2 + ur')\b', unicode(wl2), flags=re.U | re.I)
                                        if len(checkWLReg2) == 0:  # проверка на отсутствие конечного найденного слова во втором белом списке
                                            if reason == "":
                                                reason = reg2[j].lower()
                                            else:
                                                if unicode(reg2[j].lower()) not in unicode(reason):
                                                    reason += ", " + reg2[j].lower()
                                        j += 1
                                m += 1
        s += 1
    for line in bl:  # проверка на наличие слова в чёрном списке
        word4 = line.strip('\r\n')
        if (unicode("е") in unicode(line.strip('\r\n'))) or (unicode("ё") in unicode(
                line.strip('\r\n'))):  # если в слове есть е/ё, добавляем в паттерн вариабельность
            word4 = re.sub(ur'[е|ё]', u'[е|ё]', unicode(line.strip('\r\n')))
        regBl = re.findall(ur'\b(' + unicode(word4) + ur')\b', unicode(diff_text), flags=re.U | re.I)
        if len(regBl) > 0:
            if reason == "":
                reason = line.strip('\r\n').lower()
            else:
                if unicode(line.strip('\r\n').lower()) not in unicode(reason):
                    reason += ", " + line.strip('\r\n').lower()
                    			

    if reason <> "":  # вывод: если есть подозрительные слов
        prePub = "{{User:IluvatarBot/Подозрительная правка|" + str(title) + "|" + str(oldid) + "|" + str(
            revid) + "|" + str(reason) + "|" + str(int(time.time())) + "}}"


        if (oldid == '0'):
            oldidbot = oldid
            diffid = 0
        else:
            oldidbot = oldid
            diffid = revid
        payload2 = {'type': 'fem', 'user': str(user), 'oldid': str(oldidbot), 'diff': str(
            diffid), 'title': str(title), 'reason': str(reason), 'bottoken': bottoken}
        r2 = requests.post('https://tools.wmflabs.org/iluvatarbot/remove.php', data=payload2)

        pub.append(prePub)
    if len(pub) > 0:
        w = 0
        pubComplete = ""
        while w <= len(pub)-1:
            pubComplete += pub[w] + "\n"
            w += 1
        return pubComplete
# конец функции проверки и выгрузки отчёта

# Запрашиваем все списки (список профессий, белый список (сущ. в имен.падеже), конечный белый список, чёрный список), файл с последним таймстампом, id последней проверенной ревизии
try:
    URL_BL = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Феминитивы/Badlist'
    bl = urllib2.urlopen(URL_BL).readlines()
    URL_WL = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Феминитивы/Whitelist'
    wl = urllib2.urlopen(URL_WL).read()
    URL_WL2 = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Феминитивы/Whitelist2'
    wl2 = urllib2.urlopen(URL_WL2).read()
    listWorks = open('pyBot/list_of_works.txt')
    listP = listWorks.read()
    listWorks.close()
    timest = ""
    timeid = ""
    with open('pyBot/time.txt') as Lines:
        line = Lines.read().splitlines()
    timest = line[0]
    timeid = line[1]
except urllib2.HTTPError:
    print "Http error during donwloading lists"
    exit()

token, cookies = login.login()  # логинимся
try: #Запрашиваем список новых правок
    payload = {'action': 'query', 'format': 'json', 'list': 'recentchanges', 'rcnamespace': '0|6|10|12|14',
               'rcprop': 'title|ids|user|timestamp', 'rcshow': '!redirect|!bot', 'rcend': timest, 'rctype': 'new|edit', 'rclimit': limit,
               'token': token}
    json_parsed = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies).json()
except requests.exceptions.RequestException:
    print "Http error during get list of edits"
    exit()
i = -1
pb = ""
pb2 = ""
while i < len(json_parsed['query']['recentchanges']) - 1:
    i += 1
    try:
        if i == 0:
            timest = json_parsed['query']['recentchanges'][i]['timestamp']
            timeid = json_parsed['query']['recentchanges'][i]['revid']
        if not json_parsed['query']['recentchanges'][i]['revid'] == timeid:
            if str(json_parsed['query']['recentchanges'][i]['old_revid']) == "0":  # если это новая странца
                URL1 = "https://ru.wikipedia.org/w/?action=raw&utf8=1&title=" + urllib2.quote(
                    unicode(json_parsed['query']['recentchanges'][i]['title']).encode('utf8'))
                pb = check(wl, json_parsed['query']['recentchanges'][i]['title'], URL1, urllib2.urlopen(URL1).read(),
                           str(json_parsed['query']['recentchanges'][i]['revid']), 0, str(json_parsed['query']['recentchanges'][i]['user']))
            else:  # если это обычная правка на существующей странице
                URL1 = "https://ru.wikipedia.org/w/api.php?action=compare&format=json&prop=diff&utf8=1&fromrev=" + str(
                    json_parsed['query']['recentchanges'][i]['old_revid']) + "&torev=" + str(
                    json_parsed['query']['recentchanges'][i]['revid'])
                diff = ""
                diff_parsed0 = requests.post(URL1)
                diff_parsed = diff_parsed0.json()
                for chengeDiff in BeautifulSoup(diff_parsed['compare']['*']).findAll("ins", {
                    "class": "diffchange diffchange-inline"}):  # Вытаскиваем из диффа изменённые слова
                    diff += str(chengeDiff) + "\n"
                for diffAdd in BeautifulSoup(diff_parsed['compare']['*']).findAll(
                        "tr"):  # Вытаскиваем из диффа просто новые строки
                    if not "diffchange diffchange-inline" in str(diffAdd) and not "diff-deletedline" in str(diffAdd):
                        for diffAdd2 in BeautifulSoup(str(diffAdd)).findAll("", {"class": "diff-addedline"}):
                            diff += str(diffAdd2) + "\n"
                pb = check(wl, json_parsed['query']['recentchanges'][i]['title'], URL1, diff,
                           str(json_parsed['query']['recentchanges'][i]['revid']),
                           str(json_parsed['query']['recentchanges'][i]['old_revid']), str(json_parsed['query']['recentchanges'][i]['user']))

            if pb:
                pb2 += pb

    except urllib2.HTTPError as he: # удалённые и переименновые без перенаправления странцы
        print "Http error during main loop: " + str(he) + ". (" + URL1 + ")"
    except requests.exceptions.RequestException as rex: # удалённые и переименновые без перенаправления странцы
        print "Rrquest error during main loop: " + str(rex) + ". (" + URL1 + ")"
    except ValueError as ve:  # неудачные запросы (лаг сервера и тп). В общем случае: битый JSON
        print "JSON error during main loop: " + str(ve) + ". (" + URL1 + ")" + " [" + str(diff_parsed0) + "]"
    except HTMLParseError as pe: # ошибка парсинга
        print "HTMLParse error during main loop: " + str(pe) + ". (" + URL1 + ")"
    except KeyError as ke: # скрытые версии
        print "KeyError (bt) error during main loop: " + str(ke) + ". (" + URL1 + ")"

if pb2 <> "":  # если переменная с результатам не пуста, публикуем. Предварительно выпиливая уведомления, размещённые более чем указанное кол-во дней назад
    time.sleep(1)
    raportPage_URL = "https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Феминитивы/Отчёт"
    try:
        raport_page = urllib2.urlopen(raportPage_URL).readlines()
    except urllib2.HTTPError as e:
        print "Error during get raport_page (" + str(e) + ")."
        exit()
    new_pub = []
    for line2 in raport_page: # удаляем устаревшие шаблоны
        timeReg = re.findall(ur"(\d*)?\}\}", unicode(line2.strip('\r\n')), re.U | re.I)
        if not len(timeReg) > 0:
            print "Timestamp error " + u"(один из шаблонов на странице не имеет отметки времени)"
            exit()
        timePast = int(time.time()) - int(timeReg[0])
        hoursPast = int(days_history) * 24 * 60 * 60
        if not timePast >= int(hoursPast):
            new_pub.append(line2)
        raport_page = ''.join(new_pub)
    raport_page = pb2 + raport_page
    payload = {'action': 'edit', 'format': 'json', 'title': 'User:IluvatarBot/Феминитивы/Отчёт', 'utf8': '',
                   'text': raport_page,
                   'summary': 'Выгрузка отчёта', 'token': token}
    time.sleep(1)
    try:
        reqF = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
    except requests.exceptions.RequestException as e:
        print "Error during get publishing (" + str(e) + ")."
        exit()
     #print pb2   Закоментировано для снижения веса лога на Лабсе

if not str(timest) == "" and not str(timeid) == "":
    time_file = open("pyBot/time.txt", "w")
    time_file.write(str(timest).replace("Z", ".000Z") + "\n" + str(timeid))
    time_file.close()
    try: # делаем нулевую правку
        null_edit_page = urllib2.urlopen(
            'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Феминитивы').read()
        payload = {'action': 'edit', 'format': 'json', 'title': 'User:IluvatarBot/Феминитивы', 'utf8': '',
                   'text': null_edit_page,
                   'summary': 'null edit', 'token': token}
        nullReq = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
    except urllib2.HTTPError:
        print "Http error during doing null edit"
        exit()
    #print "Отчёт выгружен" Закоментировано для снижения веса лога на Лабсе