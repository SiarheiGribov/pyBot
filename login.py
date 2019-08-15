# -*- coding: utf-8 -*-

import re
import time
import requests

# Copyright © 2017, [[user:Iluvatar]], MITL; Based on https://www.mediawiki.org/wiki/User:Sebelino7/Login_with_Python

def checkLogin():
    # функця повтора логина в случае неудачи
    print('Повторная попытка входа будет произведена через 6 минут...')
    time.sleep(360)
    login()

def login(server="ru.wikipedia"):
    # Username, BotPassword, User-Agent
    with open('pyBot/password.password') as Lines:
        line = Lines.read().splitlines()
    headers = {'User-Agent': 'pyBot (iluvatarbot@tools.wmflabs.org) requests / Login'}
    # Первый этап
    req = {'action': 'query', 'format': 'json', 'utf8': '', 'meta': 'tokens', 'type': 'login'}
    r1 = requests.post('https://' + str(server) + '.org/w/' + 'api.php', data=req, headers=headers)
    login_token = r1.json()['query']['tokens']['logintoken']
    # Второй этап
    req = {'action': 'login', 'format': 'json', 'utf8': '', 'lgname': line[0], 'lgpassword': line[1], 'lgtoken': login_token}
    r2 = requests.post('https://' + str(server) + '.org/w/' + 'api.php', data=req, cookies=r1.cookies, headers=headers)
    cookies = r2.cookies
    # Получение токена для редактирования
    params3 = '?format=json&action=query&meta=tokens&continue='
    r3 = requests.get('https://' + str(server) + '.org/w/' + 'api.php' + params3, cookies=r2.cookies, headers=headers)
    # если логин не удался (не получили токен), повторяем попытку
    if not re.findall(r'\w{40}\+\\', r3.json()['query']['tokens']['csrftoken']):
        print('Не удалось войти в систему. Повторите попытку.')
        checkLogin()
    token = r3.json()['query']['tokens']['csrftoken']
    return token, cookies
