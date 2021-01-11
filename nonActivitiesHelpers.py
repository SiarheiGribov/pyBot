# -*- coding: utf-8 -*-

import requests
import re
import urllib
import datetime
import login

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

days = 30 # допустимое количество дней неактивности

# Запрашиваем страницу с подписями и берём имена
def findHelpers(pageid):
    URL = "https://ru.wikipedia.org/?curid=" + str(pageid) + "&action=raw&section=1"
    html = urllib.urlopen(URL).readlines()
    lines = []
    for line in html:
        user = re.findall(r'^\*\s*?\[\[Участни(?:к|ца):(.*?)\]\]\s*?\|', line, re.U)
        if user and not user[0] == "":
            # Для каждого найденного юзера смотрм последнюю дату правки
            URL = 'https://ru.wikipedia.org/w/api.php?action=query&format=json&list=usercontribs&uclimit=1&ucuser=' + \
                  user[0] + '&ucprop=timestamp'
            pretime = urllib.urlopen(URL).read()
            time = re.findall(r'timestamp":"(.*?)T', pretime)
            for userTime in time:
                diffTime = datetime.datetime.now() - datetime.datetime.strptime(userTime, '%Y-%m-%d')
                if diffTime.days > days:
                    lines.append(user[0])

    # если неактивные участники найдены, убираем элементы с их упоминанием из перменной со страницей
    # и форумируем массив данных для публикации
    if len(lines) > 0:
        html2 = []
        for htmlLine in html:
            check = "false"
            j = 0
            while (check == "false" and not j > len(lines) - 1):
                if lines[j] in htmlLine:
                    check = "true"
                else:
                    j = j + 1
            if check == "false":
                html2.append(htmlLine)
        html2 = ''.join(html2)

        # формируем массив данных для публикации на странице-оповещении
        URL = 'https://ru.wikipedia.org/?curid=6923674&action=raw'
        html = urllib.urlopen(URL).readlines()
        notif = ""
        for notify in lines:
            print "Участник " + notify + " неактивен более " + str(days) + " дн."  # и заодно выводим инфу в консоль
            notif = notif + "\n* {{Ping|" + notify + "}} у вас отсутствуют правки на протяжении " + str(
                days) + " дн. По возвращении в проект, пожалуйста, добавьте себя повторно в "
            notif = notif + "[[Проект:Помощь начинающим/Приветствующие|список приветствующих]].--~~~~" if pageid == 1006803 else notif + "[[Проект:Помощь начинающим/Наставники|список наставников]].--~~~~"
        html = ''.join(html) + notif

        # производим логин, получаем куки и токен
        token, cookies = login.login()
        # производим отправку на сервер нового списка участников и страницы оповещений

        payload = {'action': 'edit', 'format': 'json', 'pageid': pageid, 'section': 1, 'utf8': '', 'text': html2,
                   'summary': 'Удаление неактивных более ' + str(days) + ' дн. участников', 'token': token}
        requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
        summary = 'Оповещение неактивного приветствующего' if pageid == 1006803 else 'Оповещение неактивного наставника'
        payload = {'action': 'edit', 'format': 'json', 'pageid':  6923674, 'utf8': '',
                   'text': html, 'summary': summary, 'token': token}
        requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)

        print "Список помощников/наставников обновлён; оповещение произведено."

findHelpers(1006803)
findHelpers(8409309)

# print "Проверка завершена."