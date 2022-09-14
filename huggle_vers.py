#!/usr/bin/env python3
# coding: utf8

import login
import requests


def send(ver):
    token, cookies = login.login()
    payload = {'action': 'edit', 'format': 'json', 'title': 'Template:Huggle/Version', 'utf8': '', 'text': ver,
               'summary': 'Обновление номера версии', 'token': token}
    try:
        requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
    except:
        print(u"Ошибка при публикации")
        exit()


try:
    URL_VER_ORIG = 'https://en.wikipedia.org/w/?action=raw&utf8=1&title=Template:Huggle/Version'
    VER_ORIG = requests.get(URL_VER_ORIG).text.rstrip('\n')
    URL_VER_OLD = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=Template:Huggle/Version'
    VER_OLD = requests.get(URL_VER_OLD).text.rstrip('\n')
    if VER_OLD != VER_ORIG:
        send(VER_ORIG)
except:
    print(u"Ошибка при получении содержимого шаблонов.")
    exit()
