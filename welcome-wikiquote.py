# coding=utf-8

import re
import login
import datetime
import requests
from random import randrange

minutes = 23
signUrl = 'https://ru.wikiquote.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Sign'

token, cookies = login.login(server="ru.wikiquote")

# Список подписей и чёрный список
signList = []
signData = requests.get(signUrl).text.splitlines()
for line in signData:
    line = str(line.rstrip('\n'))
    if re.match(r'^\*', line):
        signList.append('{{subst:Welcome}}\n\n' + re.sub(r'^\*\s', '', line) + ' ~~~~~')
# Получаем список юзеров из свежих правок
payload = {'action': 'query', 'format': 'json', 'list': 'recentchanges',
           'rcprop': 'user|timestamp', 'rcshow': '!bot|!anon', 'rctype': 'new|edit',
           'rcend': (datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)).strftime(
               "%Y-%m-%d %H:%M:%S"), 'rclimit': 5000}
r_changes = requests.post('https://ru.wikiquote.org/w/api.php', data=payload, cookies=cookies).json()
users = r_changes["query"]["recentchanges"]
# Чтобы не запрашивались повторно данные о юзере, сделавшем несколько правок
usersCheck = []
usersList = ''
for user in users:
    if "user" in user:
        if user['user'] not in usersCheck:
            usersCheck.append(user['user'])
            usersList += user['user'] + '|'
# Проверяем число правок и не заблокирован ли юзер
payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'users', 'ususers': usersList.rstrip('|'),
           'usprop': 'blockinfo|editcount', 'token': token}
r_userinfo = requests.post('https://ru.wikiquote.org/w/api.php', data=payload, cookies=cookies).json()
userinfo = r_userinfo["query"]["users"]
for user in userinfo:
    if ('blockid' not in user) and ('invalid' not in user):
        if (user['editcount'] > 0) and (user['editcount'] < 25):
            # Проверяем, не была ли у юзера удалена ЛСО
            payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'logevents', 'letype': 'delete',
                       'letitle': 'User talk:' + user['name']}
            r_isdelete = requests.post("https://ru.wikiquote.org/w/api.php", data=payload, cookies=cookies).json()
            if len(r_isdelete["query"]["logevents"]) == 0:
                # Если имя не заканчивается на бот / bot
                if not (re.search(r'(бот|bot|Бот)$', user['name'], flags=re.I)):
                    # Публикуем приветствие, если страница ещё не создана.
                    random_index = randrange(0, len(signList))
                    sign = signList[random_index]
                    payload = {'action': 'edit', 'format': 'json', 'title': 'User talk:' + user['name'],
                               'utfl8': '',
                               'createonly': '1', 'recreate': '0', 'notminor': '', 'text': sign,
                               'summary': u'Добро пожаловать!', 'token': token}
                    r_edit = requests.post('https://ru.wikiquote.org/w/api.php', data=payload, cookies=cookies)
