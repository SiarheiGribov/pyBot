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
signUrl = 'https://ru.wikiquote.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Sign'

token, cookies = login.login()

# Список подписей и чёрный список
signList = []
signData = urlopen(signUrl).readlines()
for line in signData:
    line = str(line.decode('UTF-8').rstrip('\n'))
    if re.match(r'^\*', line):
        signList.append('{{Welcome}} ' + re.sub(r'^\*\s', '', line) + ' ~~~~~')
# Получаем список юзеров из свежих правок
payload = {'action': 'query', 'format': 'json', 'list': 'recentchanges',
'rcprop': 'user|timestamp', 'rcshow': '!bot|!anon', 'rctype': 'new|edit', 'rcend': (datetime.datetime.now() - datetime.timedelta(minutes = minutes)).strftime("%Y-%m-%d %H:%M:%S"), 'rclimit': 5000, 'token': token}
r_changes = json.loads(requests.post('https://ru.wikiquote.org/w/api.php', data=payload, cookies=cookies).text)
users = ast.literal_eval('{query}'.format(**r_changes))
users = ast.literal_eval('{recentchanges}'.format(**users))
#Чтобы не запрашивались повторно данные о юзере, сделавшем несколько правок
usersCheck = []
usersList = ''
for user in users:
    if user['user'] not in usersCheck:
        usersCheck.append(user['user'])
        usersList += user['user'] + '|'
# Проверяем число правок и не заблокирован ли юзер
payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'users', 'ususers': usersList.rstrip('|'), 'usprop': 'blockinfo|editcount', 'token': token}
r_userinfo = json.loads(requests.post('https://ru.wikiquote.org/w/api.php', data=payload, cookies=cookies).text)
userinfo = ast.literal_eval('{query}'.format(**r_userinfo))
userinfo = ast.literal_eval('{users}'.format(**userinfo))
for user in userinfo:
    if ('blockid' not in user) and ('invalid' not in user):
        if (user['editcount'] > 0) and (user['editcount'] < 25):
            # Проверяем, не была ли у юзера удалена ЛСО
            payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'logevents', 'letype': 'delete', 'letitle': 'User talk:' + user['name'], 'token': token}
            r_isdelete = json.loads(requests.post('https://ru.wikiquote.org/w/api.php', data=payload, cookies=cookies).text)
            isdelete = ast.literal_eval('{query}'.format(**r_isdelete))
            isdelete = ast.literal_eval('{logevents}'.format(**isdelete))
            if len(isdelete) == 0:
                # Если имя не заканчивается на бот / bot
                if not (re.search(r'[бот|bot]$', user['name'])):
                    # Публикуем приветствие, если страница ещё не создана.
                    random_index = randrange(0, len(signList))
                    sign = signList[random_index]
                    payload = {'action': 'edit', 'format': 'json', 'title': 'User talk:' + user['name'], 'utfl8': '', 'createonly': '', 'notminor': '', 'text': sign, 'summary': u'Добро пожаловать!', 'token': token}
                    r_edit = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
