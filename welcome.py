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

minutes = 33
signUrl = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:LatitudeBot/Sign'

token, cookies = login.login()


signList = []
signData = urlopen(signUrl).readlines()
for line in signData:
    line = str(line.decode('UTF-8').rstrip('\n'))
    if re.match(r'^\*', line):
        signList.append('{{Hello}} ' + re.sub(r'^\*\s', '', line) + ' ~~~~~')
r_users = []

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
payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'users', 'ususers': usersList.rstrip('|'), 'usprop': 'blockinfo|editcount|groups', 'token': token}
r_userinfo = json.loads(requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies).text)
userinfo = ast.literal_eval('{query}'.format(**r_userinfo))
userinfo = ast.literal_eval('{users}'.format(**userinfo))
for user in userinfo:
    if ('blockid' not in user) and ('invalid' not in user):
        if (user['editcount'] > 0) and (user['editcount'] < 25):
            payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'logevents', 'letype': 'delete', 'letitle': 'User talk:' + user['name'], 'token': token}
            r_isdelete = json.loads(requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies).text)
            isdelete = ast.literal_eval('{query}'.format(**r_isdelete))
            isdelete = ast.literal_eval('{logevents}'.format(**isdelete))
            if len(isdelete) == 0:
                r_users.append(user['name'])

for r_user in r_users:
    random_index = randrange(0, len(signList))
    sign = signList[random_index]
    payload = {'action': 'edit', 'format': 'json', 'title': 'User talk:' + r_user, 'utf8': '', 'createonly': '', 'notminor': '', 'text': sign, 'summary': u'Добро пожаловать!', 'token': token}
    r_edit = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
