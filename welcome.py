# coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('pyBot/ext_libs')
import re
import ast
import json
import time
import login
import datetime
import requests
from urllib2 import urlopen
from random import randrange
from sseclient import SSEClient as EventSource

minutes = 23
signUrl = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:LatitudeBot/Sign'

token, cookies = login.login()

# Список подписей и чёрный список
signList = []
signData = urlopen(signUrl).readlines()
for line in signData:
    line = str(line.decode('UTF-8').rstrip('\n'))
    if re.match(r'^\*', line):
        signList.append('{{Hello}} ' + re.sub(r'^\*\s', '', line) + ' ~~~~~')
badList = []
URL_BL = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Badlist'
bl = urlopen(URL_BL).readlines()
for line in bl:
    line = str(line.decode('UTF-8').rstrip('\n'))
    if re.match(r'^\*', line):
        badList.append(re.sub(r'^\*', '', line))
# Получаем список юзеров из свежих правок
payload = {'action': 'query', 'format': 'json', 'list': 'recentchanges',
'rcprop': 'user|timestamp', 'rcshow': '!bot|!anon', 'rctype': 'new|edit', 'rcend': (datetime.datetime.now() - datetime.timedelta(minutes = minutes)).strftime("%Y-%m-%d %H:%M:%S"), 'rclimit': 5000, 'token': token}
r_changes = json.loads(requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies).text)
users = ast.literal_eval('{query}'.format(**r_changes))
users = ast.literal_eval('{recentchanges}'.format(**users))
usersCheck = []
usersList = ''
for user in users:
    if user['user'] not in usersCheck:
        usersCheck.append(user['user'])
        usersList += user['user'] + '|'
# Проверяем число правок и не заблокирован ли юзер
payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'users', 'ususers': usersList.rstrip('|'), 'usprop': 'blockinfo|editcount', 'token': token}
r_userinfo = json.loads(requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies).text)
userinfo = ast.literal_eval('{query}'.format(**r_userinfo))
userinfo = ast.literal_eval('{users}'.format(**userinfo))
for user in userinfo:
    if ('blockid' not in user) and ('invalid' not in user):
        if (user['editcount'] > 0) and (user['editcount'] < 25):
            # Проверяем, не была ли у юзера удалена ЛСО
            payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'logevents', 'letype': 'delete', 'letitle': 'User talk:' + user['name'], 'token': token}
            r_isdelete = json.loads(requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies).text)
            isdelete = ast.literal_eval('{query}'.format(**r_isdelete))
            isdelete = ast.literal_eval('{logevents}'.format(**isdelete))
            if len(isdelete) == 0:
                # Если имя не заканчивается на бот / bot
                if not (re.search(r'[бот|bot]$', user['name'])):
                    # Публикуем приветствие, если страница ещё не создана. Также проверяем имя на наличие в нём
                    # элементов из чёрного списка и при необходимости публикуем отчёт
                    reason = ''
                    new_pub = []
                    for badWord in badList:
                        if (re.search(r'' + badWord, user['name'], re.I)):
                            reason += re.sub(r'\\', '', badWord) + ','
                    if not reason == '':
                        pre_pub = '{{Подозрительное имя учётной записи|' + user['name'] + '|' + reason.rstrip(',') + '}}'
                        URL_RAPORT = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Report'
                        raport = urlopen(URL_RAPORT).readlines()
                        for line in raport:
                            if not line.decode("utf-8").strip('\r\n') == '{{/header}}':
                                new_pub.append(line.decode("utf-8").strip('\r\n'))
                        raport_page = ''.join(map(str,new_pub))
                        raport_page = '{{/header}}' + pre_pub + raport_page
                        payload = {'action': 'edit', 'format': 'json', 'title': 'User:IluvatarBot/Report', 'utf8': '', 'text': raport_page, 'summary': 'Выгрузка отчёта: подозрительный ник', 'token': token}
                        r_bad = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
                    random_index = randrange(0, len(signList))
                    sign = signList[random_index]
                    payload = {'action': 'edit', 'format': 'json', 'title': 'User talk:' + user['name'], 'utf8': '', 'createonly': '', 'notminor': '', 'text': sign, 'summary': u'Добро пожаловать!', 'token': token}
                    r_edit = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
