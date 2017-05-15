# -*- coding: utf-8 -*-

import requests
import re
import urllib
import time
import datetime
import login
import os
import sys

#Copyright (c) 2017, [[user:Iluvatar]]
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


reload(sys)
sys.setdefaultencoding('utf8')

if os.path.exists("pyBot/result.txt"):
    os.remove("pyBot/result.txt")

def check(target):
    target_safe = urllib.quote_plus(target)
    target2 = re.findall('^Шаблон:(.*)', target)
    rep = 0
    html2 = ""
    txt = ""

    checkWhile = "true"
    checkCont = "false"

    # Получаем все включения шаблона
    while (checkWhile == "true"):
        if checkCont == "false":
            URL = 'https://ru.wikipedia.org/w/api.php?action=query&list=embeddedin&eititle=' + target_safe + '&eilimit=500&eifilterredir=all&format=json'
        else:
            URL = 'https://ru.wikipedia.org/w/api.php?action=query&list=embeddedin&eititle=' + target_safe + '&eilimit=500&eicontinue=' + cont_safe + '&eifilterredir=all&format=json'

        while True:
            try:
                html = urllib.urlopen(URL).read()
            except:
                time.sleep(20)
            else:
                break

        if "eicontinue" in html:
            checkWhile = "true"
            checkCont = "true"
            cont = re.findall(r'^.*?eicontinue\":\"(.*?)\"\,', html.decode('unicode-escape').encode('utf8'))
            cont_safe = urllib.quote_plus(cont[0])
        else:
            checkWhile = "false"
            checkCont = "false"

        html2 = html2 + html.decode('unicode-escape').encode('utf8')

    # Получаем имена страниц
    title = re.findall(r'title\":\"(.*?)\"\}', html2)

    n = 0
    print "\033[92mВсего страниц для проверки по шаблону "+ target2[0] + ": " + str(len(title)) + ". Проверка может занять длительное время.\033[0m"

    # Получаем все ссылки, которые имеются на странице(в 4 пространстве имён) и вытаскиваем их них мя страницы номинации
    while n <= len(title) - 1:
        if not target in title[n] and not "Википедия:Шаблоны/Перемещение содержимого" == title[n] and not "Википедия:Шаблоны/Удаление содержимого" == title[n] and not "Шаблон:Неиспользуемые шаблоны" in title[n]:
            if '"redirect":' in title[n]:
                redir = re.findall(r'^(.*?)\"\,\"redirect\"', title[n])
                title[n] = redir[0]
            title_safe = urllib.quote_plus(title[n])
            URL = "https://ru.wikipedia.org/w/api.php?action=query&format=json&prop=links&plnamespace=4&titles=" + title_safe + "&pllimit=500"
            while True:
                try:
                    html = urllib.urlopen(URL).read()
                except:
                    time.sleep(20)
                else:
                    break

            if not '"missing": ""' in html.decode('unicode-escape').encode('utf8'):
                link = re.findall(r'title\":\"(Википедия:' + target2[0] + '\/.*?)\"\}',
                                  html.decode('unicode-escape').encode('utf8'))

                # Проверяем, ссылается ли страница номинации с указанным именем на статью
                checkWhile = "true"
                checkCont = "false"
                while (checkWhile == "true"):
                    if checkCont == "false":
                        URL = 'https://ru.wikipedia.org/w/api.php?action=query&list=backlinks&bltitle=' + title_safe + '&bllimit=250&blredirect&blnamespace=0|4&format=json'
                    else:
                        URL = 'https://ru.wikipedia.org/w/api.php?action=query&list=backlinks&bltitle=' + title_safe + '&bllimit=250&blcontinue=' + cont_safe + '&blredirect&blnamespace=0|4&format=json'

                    while True:
                        try:
                            html = urllib.urlopen(URL).read()
                        except:
                            time.sleep(20)
                        else:
                            break

                    if "blcontinue" in html:
                        checkWhile = "true"
                        checkCont = "true"
                        cont = re.findall(r'^.*?blcontinue\":\"(.*?)\"\,', html.decode('unicode-escape').encode('utf8'))
                        cont_safe = urllib.quote_plus(cont[0])
                    else:
                        checkWhile = "false"
                        checkCont = "false"

                    txt = txt + html.decode('unicode-escape').encode('utf8')

                if not len(link) > 0:
                    if rep == 0:
                        text = "'''{{tl|" + target2[0] + "}}:'''<br />\n# [[:" + title[
                            n] + "]]: шаблон снят, либо в нём не указана дата"
                        rep = 1
                    else:
                        text = "# [[:" + title[n] + "]]: шаблон снят, либо в нём не указана дата"
                    if os.path.exists("pyBot/result.txt"):
                        my_file = open("pyBot/result.txt", "a")
                    else:
                        my_file = open("pyBot/result.txt", "w")
                    my_file.write(text.encode('utf8') + "\n")
                    my_file.close()
                    print "\033[91m" + title[n] + ": нет параметра даты\033[0m"
                else:
                    if not link[0] in txt:
                        if rep == 0:
                            text = "'''{{tl|" + target2[0] + "}}:'''<br />\n# [[:" + title[n] + "]]: [[" + link[0] + "]]"
                            rep = 1
                        else:
                            text = "# [[:" + title[n] + "]]: [[" + link[0] + "]]"
                        if os.path.exists("pyBot/result.txt"):
                            my_file = open("pyBot/result.txt", "a")
                        else:
                            my_file = open("pyBot/result.txt", "w")
                        my_file.write(text.encode('utf8') + "\n")
                        my_file.close()
                        print '\033[91m' + title[n] + ': ' + link[0] + '\033[0m'


            #print '\033[94m(' + str(len(title) - n - 1) + ") " + title[n] + '\033[0m'   Закомментировано для уменьшения лога на Лабсе
            n = n + 1
        else:
            #print '\033[94m(' + str(len(title) - n - 1) + ") " + title[n] + '\033[0m'   Закомментировано для уменьшения лога на Лабсе
            n = n + 1

    # Добавляем пустую строку перел отчётом по следующему заданию
    if os.path.exists("pyBot/result.txt"):
        my_file = open("pyBot/result.txt", "a")
        my_file.write("<br>\n")
        my_file.close()
    print "\033[92mРабота по шаблону " + target2[0] + " завершена. Всего проверено страниц: " + str(len(title)) + ".\033[0m"



# вызываем функцию для всех шаблонов
check("Шаблон:К удалению")
check("Шаблон:К объединению")
check("Шаблон:К разделению")
check("Шаблон:К переименованию")
check("Шаблон:К улучшению")

# если файл с отчётом не пустой, загружаем отчёт
if os.path.exists("pyBot/result.txt"):
    token, cookies = login.login()      # логинимся
    my_file = open("pyBot/result.txt", "r")
    text = my_file.read()
    text = ":'''''" + datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M") + "''''' (UTC)\n\n" + text
    my_file.close()
    payload = {'action': 'edit', 'format': 'json', 'title': 'User:IluvatarBot/Мониторинг шаблонов', 'utf8': '', 'text': text,
               'summary': 'Выгрузка отчёта', 'token': token}
    r4 = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
    os.remove("pyBot/result.txt")
    print "\033[92mОтчёт загружен.\033[0m"

