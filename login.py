# -*- coding: utf-8 -*-

import time
import requests

headers = {'User-Agent': 'pyBot (iluvatarbot@tools.wmflabs.org); python (requests); Login'}


def login_retry():
    time.sleep(360)  # 6 мин
    login()


def login(server="ru.wikipedia"):
    with open('pyBot/password.password') as lines:
        lines = lines.read().splitlines()
        username = lines[0]  # BotUsername
        password = lines[1]  # BotPassword

    req = {'action': 'query', 'format': 'json', 'utf8': '', 'meta': 'tokens', 'type': 'login'}
    r1 = requests.post('https://' + str(server) + '.org/w/' + 'api.php', data=req, headers=headers)
    login_token = r1.json()['query']['tokens']['logintoken']

    req = {'action': 'login', 'format': 'json', 'utf8': '', 'lgname': username, 'lgpassword': password,
           'lgtoken': login_token}
    r2 = requests.post('https://' + str(server) + '.org/w/' + 'api.php', data=req, cookies=r1.cookies, headers=headers)
    cookies = r2.cookies

    params3 = '?format=json&action=query&meta=tokens'
    r3 = requests.get('https://' + str(server) + '.org/w/' + 'api.php' + params3, cookies=r2.cookies, headers=headers)

    if r3.json()['query']['tokens']['csrftoken'] == "+\\":
        login_retry()

    token = r3.json()['query']['tokens']['csrftoken']
    return token, cookies
