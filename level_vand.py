#!/usr/bin/env python3
# coding: utf8

#MIT License
#Copyright (c) 2017 Siarhei Gribov, [[User:Iluvatar]].
#The idea is borrowed from https://github.com/enterprisey/EnterpriseyBot/blob/master/LICENSE.md
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

import re
import ast
import sys
import time
import json
import login
import datetime
import requests
from urllib.parse import urlparse
from urllib.parse import quote
from urllib.request import urlopen

minutes = 60    # интервал в минутах
coefficient = 4 # коэффициент, корректирующий рассчёт уровня вандализма для конкретного проекта (от числа правок в минуту. В англовики — 1, в рувики общее число правок в минуту меньше прибл. в 4-5 раз)
words = ("revert", "откат", "rv ", "отмена", "rvv ", "undid", "отклонено последнее", "отклонены последние", "вандализм")



token, cookies = login.login()

header = re.compile(r"/\*[\s\S]+?\*/")
def calc(cont, res):
    i = res
    if cont!=-1 and cont!=-2:
        payload = {'action': 'query', 'format': 'json', 'list': 'recentchanges',
               'rcprop': 'comment', 'rcend': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'rcend': (datetime.datetime.now() - datetime.timedelta(minutes = minutes)).strftime("%Y-%m-%d %H:%M:%S"), 'rclimit': 5000, 'rctype': 'edit', 'rccontinue': cont}
    else:
        payload = {'action': 'query', 'format': 'json', 'list': 'recentchanges',
               'rcprop': 'comment', 'rcend': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'rcend': (datetime.datetime.now() - datetime.timedelta(minutes = minutes)).strftime("%Y-%m-%d %H:%M:%S"), 'rclimit': 5000, 'rctype': 'edit'}
    try:
        req = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
    except requests.exceptions.RequestException:
        print("Http error during get list recent changes")
        sys.exit()
    data = json.loads(req.text)
    for line in data['query']['recentchanges']:
        if not "commenthidden" in line:
            comment = header.sub("", '{comment}'.format(**line).lower())
            if not comment == "":
                if any(elem in comment for elem in words):
                    i += 1
    if "continue" in data:
        rccontinue = '{rccontinue}'.format(**data['continue'])
    else:
        rccontinue = -1
    return rccontinue, i


res=0
cont=-2
while cont!=-1:
    cont, res = calc(cont, res)
    time.sleep(1)

if res==0:
    VAND_NEW = 5
else:
    if res*coefficient/minutes <= 8:
        VAND_NEW = 2
    if res*coefficient/minutes <= 6:
        VAND_NEW = 3
    if res*coefficient/minutes <= 4:
        VAND_NEW = 4
    if res*coefficient/minutes <= 2:
        VAND_NEW = 5
    if res*coefficient/minutes > 8:
        VAND_NEW = 1

URL_VAND_OLD = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/' + quote('Уровень вандализма/уровень')
VAND_PAGE = urlopen(URL_VAND_OLD).readlines()
level = re.search("level\s*?=\s*?(\d+)", str(VAND_PAGE))
    

if not str(level.group(1)) == str(VAND_NEW):
    VAND_PAGE_NEW = r"{{#switch:{{{1}}}|level=" + str(VAND_NEW) + "|sign=~~~~~|info=" + str(round(res/60, 1)) + " RPM по информации [[User:IluvatarBot|IluvatarBot]]}}"
    payload = {'action': 'edit', 'format': 'json', 'title': 'User:IluvatarBot/Уровень вандализма/уровень', 'utf8': '', 'text': VAND_PAGE_NEW, 'summary': 'Обновление данных', 'token': token}
    try:
        req = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
		
    except:
        print(u"Error during publish")
        pass
