# -*- coding: utf-8 -*-

import datetime
import re
import requests
import login

days = 30  # допустимое количество дней неактивности


# Запрашиваем страницу с подписями и берём имена
def find_helpers(pageid):
    url = "https://ru.wikipedia.org/?curid=" + str(pageid) + "&action=raw&section=1"
    html = requests.get(url).text.splitlines()
    lines = []
    for line in html:
        user = re.findall(r'^\*\s*?\[\[Участни(?:к|ца):(.*?)]]\s*?\|', line, re.U)
        if user and not user[0] == "":
            # Для каждого найденного юзера смотрим последнюю дату правки
            url = 'https://ru.wikipedia.org/w/api.php?action=query&format=json&list=usercontribs&uclimit=1&ucuser=' + \
                  user[0] + '&ucprop=timestamp'
            pretime = requests.get(url).text
            time = re.findall(r'timestamp":"(.*?)T', pretime)
            for userTime in time:
                diff_time = datetime.datetime.now() - datetime.datetime.strptime(userTime, '%Y-%m-%d')
                if diff_time.days > days:
                    lines.append(user[0])

    # если неактивные участники найдены, убираем элементы с их упоминанием из перменной со страницей
    # и формируем массив данных для публикации
    if len(lines) > 0:
        html2 = []
        for htmlLine in html:
            check = "false"
            j = 0
            while check == "false" and not j > len(lines) - 1:
                if lines[j] in htmlLine:
                    check = "true"
                else:
                    j = j + 1
            if check == "false":
                html2.append("\n" + htmlLine)
        html2 = ''.join(html2)
        html2 = html2[1:]

        # формируем массив данных для публикации на странице-оповещении
        url = 'https://ru.wikipedia.org/?curid=6923674&action=raw'
        html = requests.get(url).text
        notif = ""
        for notify in lines:
            print("Участник " + notify + " неактивен более " + str(days) + " дн.")
            notif = notif + "\n* {{Ping|" + notify + "}} у вас отсутствуют правки на протяжении " + str(
                days) + " дн. По возвращении в проект, пожалуйста, добавьте себя повторно в "
            notif = notif + "[[Проект:Помощь начинающим/Приветствующие|список приветствующих]].--~~~~" \
                if pageid == 1006803 else notif + "[[Проект:Помощь начинающим/Наставники|список наставников]].--~~~~"
        html = ''.join(html) + notif

        # производим логин, получаем куки и токен
        token, cookies = login.login()
        # производим отправку на сервер нового списка участников и страницы оповещений

        payload = {'action': 'edit', 'format': 'json', 'pageid': pageid, 'section': 1, 'utf8': '', 'text': html2,
                   'summary': 'Удаление неактивных более ' + str(days) + ' дн. участников', 'token': token}
        requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
        summary = 'Оповещение неактивного приветствующего' if pageid == 1006803 else 'Оповещение неактивного наставника'
        payload = {'action': 'edit', 'format': 'json', 'pageid': 6923674, 'utf8': '',
                   'text': html, 'summary': summary, 'token': token}
        requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)

        print("Список помощников/наставников обновлён; оповещение произведено.")


find_helpers(1006803)
find_helpers(8409309)

# print "Проверка завершена."
