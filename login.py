# -*- coding: utf-8 -*-

import requests
import re
import time
import json

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

# функця повтора логна в случае неудачи
def checkLogin():
    print('У вас нет прав, либо требуется повторно войти в систему.')
    print('Повторная попытка входа будет произведена через 15 секунд...')
    time.sleep(15)
    login()

# основная функция логина
def login():
    with open('password.password') as Lines:
        line = Lines.read().splitlines()
    username = line[0]
    password = line[1]

    # Первый этап логина
    req = {'action': 'query', 'format': 'json', 'utf8': '', 'meta': 'tokens', 'type': 'login'}
    r1 = requests.post('https://ru.wikipedia.org/w/' + 'api.php', data=req)

    # Второй этап логина
    login_token = r1.json()['query']['tokens']['logintoken']
    req = {'action': 'login', 'format': 'json', 'utf8': '', 'lgname': username, 'lgpassword': password,
           'lgtoken': login_token}
    r2 = requests.post('https://ru.wikipedia.org/w/' + 'api.php', data=req, cookies=r1.cookies)
    cookies = r2.cookies

    # Получение токена для редактирования
    params3 = '?format=json&action=query&meta=tokens&continue='
    r3 = requests.get('https://ru.wikipedia.org/w/' + 'api.php' + params3, cookies=r2.cookies)
    token = r3.json()['query']['tokens']['csrftoken']
    # если логнн не удался (не получили токен), повторяем попыткук
    if not re.findall(r'.*?csrftoken....................', json.dumps(r3.json())):
        print('Не удалось войти в систему. Повторите попытку.')
        checkLogin()
    return token, cookies


