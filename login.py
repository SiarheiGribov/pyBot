# -*- coding: utf-8 -*-

import requests
import re
import time
import json

# Copyright © 2017, [[user:Iluvatar]], MITL; Based on https://www.mediawiki.org/wiki/User:Sebelino7/Login_with_Python

# функця повтора логина в случае неудачи
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
    
    # если логин не удался (не получили токен), повторяем попытку
    if not re.findall(r'.*?csrftoken....................', json.dumps(r3.json())):
        print('Не удалось войти в систему. Повторите попытку.')
        checkLogin()
    return token, cookies


