#!/usr/bin/env python3
# coding: utf8

import login
import requests
from urllib.request import urlopen

try:
    URL_VER_ORIG = 'https://en.wikipedia.org/w/?action=raw&utf8=1&title=Template:Huggle/Version'
    VER_ORIG = urlopen(URL_VER_ORIG).readline().decode('UTF-8').rstrip('\n')
    URL_VER_OLD = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=Template:Huggle/Version'
    VER_OLD = urlopen(URL_VER_OLD).readline().decode('UTF-8').rstrip('\n')
except:
    print(u"Ошибка при получении содержимого шаблонов.")
    exit()

if not VER_OLD == VER_ORIG:
    token, cookies = login.login()
    payload = {'action': 'edit', 'format': 'json', 'title': 'Template:Huggle/Version', 'utf8': '', 'text': VER_ORIG, 'summary': 'Обновление номера версии', 'token': token}
    try:
        req = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
    except:
        print(u"Ошибка при публикации")
        exit()