# coding=utf-8

import ast
import json
import re
from random import randrange
from urllib.request import urlopen
import requests
import login

signUrl = 'https://ru.wikipedia.org/?curid=1006803&action=raw&section=1'
signUrlMentors = 'https://ru.wikipedia.org/?curid=8409309&action=raw&section=1'

# Список подписей и чёрный список
signList = []
preSignList = {}
defaultPhrase = "При вопросах можете обратиться к $ "

signData = urlopen(signUrl).readlines()
signDataMentors = urlopen(signUrlMentors).readlines()

token, cookies = login.login()

# Список подписей и чёрный список
for line in signData:
    line = str(line.decode('UTF-8').rstrip('\n'))
    if re.match(r'^\*\s*?\[\[Участни(?:к|ца):(.*?)\]\]\s*?\|(.*)', line):
        r = re.match(r'^\*\s*?\[\[(Участни(?:к|ца)):(.*?)\]\]\s*?\|(.*)', line)
        preSignList[r.group(2)] = {"gender": r.group(1), "phrase": r.group(3).lstrip().rstrip() + " — ~~~~~"}
for line in signDataMentors:
    line = str(line.decode('UTF-8').rstrip('\n'))
    if re.match(r'^\*\s*?\[\[Участни(?:к|ца):(.*?)\]\]\s*?\|(.*)', line):
        r = re.match(r'^\*\s*?\[\[(Участни(?:к|ца)):(.*?)\]\]\s*?\|(.*)', line)
        if r.group(2) not in preSignList:
            preDefaultPhrase = defaultPhrase.replace("$", "участнику") if (
                    r.group(1) == "Участник") else defaultPhrase.replace("$", "участнице")
            preSignList[r.group(2)] = {"gender": r.group(1),
                                       "phrase": preDefaultPhrase + "[[ОУ:" + r.group(2) + "|" + r.group(
                                           2) + "]] — ~~~~~"}
for k in preSignList:
    signList.append('{{Hello}} ' + preSignList[k]["phrase"])

badList = []
URL_BL = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Badlist'
bl = urlopen(URL_BL).readlines()
for line in bl:
    line = str(line.decode('UTF-8').rstrip('\n'))
    if re.match(r'^\*', line):
        badList.append(re.sub(r'^\*', '', line))

with open('pyBot/timeWelcome.txt') as Lines:
    line = Lines.read().splitlines()
timestamp = line[0]
rc_id = line[1]

# Получаем список юзеров из свежих правок
payload = {'action': 'query', 'format': 'json', 'list': 'recentchanges',
           'rcprop': 'user|timestamp|ids', 'rcshow': '!bot|!anon', 'rctype': 'new|edit', 'rcend': timestamp,
           'rclimit': 5000}
r_changes = json.loads(requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies).text)
data = ast.literal_eval('{query}'.format(**r_changes))
users = ast.literal_eval('{recentchanges}'.format(**data))

usersCheck = []
usersList = ''
timestampNow = users[0]["timestamp"]
rcidNow = users[0]["rcid"]
time_file = open("pyBot/timeWelcome.txt", "w")
time_file.write(str(timestampNow) + "\n" + str(rcidNow))
time_file.close()

for user in users:
    if user['user'] not in usersCheck and int(user["rcid"]) != int(rc_id):
        usersCheck.append(user['user'])
        usersList += user['user'] + '|'
# Проверяем число правок и не заблокирован ли юзер
payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'users', 'ususers': usersList.rstrip('|'),
           'usprop': 'blockinfo|editcount', 'token': token}
r_userinfo = json.loads(requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies).text)
userinfo = ast.literal_eval('{query}'.format(**r_userinfo))
userinfo = ast.literal_eval('{users}'.format(**userinfo))
for user in userinfo:
    if ('blockid' not in user) and ('invalid' not in user):
        if (user['editcount'] > 0) and (user['editcount'] < 25):
            # Проверяем, не была ли у юзера удалена ЛСО
            payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'logevents', 'letype': 'delete',
                       'letitle': 'User talk:' + user['name'], 'token': token}
            r_isdelete = json.loads(
                requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies).text)
            isdelete = ast.literal_eval('{query}'.format(**r_isdelete))
            isdelete = ast.literal_eval('{logevents}'.format(**isdelete))
            if len(isdelete) == 0:
                # Если имя не заканчивается на бот / bot
                if not (re.search(r'(бот|bot|Бот)$', user['name'], flags=re.I)):
                    # Публикуем приветствие, если страница ещё не создана. Также проверяем имя на наличие в нём
                    # элементов из чёрного списка и при необходимости публикуем отчёт
                    reason = ''
                    new_pub = []
                    for badWord in badList:
                        if re.search(r'' + badWord, user['name'], re.I):
                            reason += re.sub(r'\\', '', badWord) + ','
                    if not reason == '':
                        pre_pub = '{{Подозрительное имя учётной записи|' + user['name'] + '|' + reason.rstrip(
                            ',') + '}}'
                        URL_RAPORT = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Report'
                        raport = urlopen(URL_RAPORT).readlines()
                        for line in raport:
                            if not line.decode("utf-8").strip('\r\n') == '{{/header}}':
                                new_pub.append(line.decode("utf-8").strip('\r\n') + "\n")
                        raport_page = ''.join(map(str, new_pub))
                        raport_page = '{{/header}}\n' + pre_pub + "\n" + raport_page
                        payload = {'action': 'edit', 'format': 'json', 'title': 'User:IluvatarBot/Report', 'utf8': '',
                                   'text': raport_page, 'summary': 'Выгрузка отчёта: подозрительный ник',
                                   'token': token}
                        r_bad = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
                    random_index = randrange(0, len(signList))
                    sign = signList[random_index]
                    payload = {'action': 'edit', 'format': 'json', 'title': 'User talk:' + user['name'], 'utf8': '',
                               'createonly': '', 'notminor': '', 'text': sign, 'summary': u'Добро пожаловать!',
                               'token': token}
                    r_edit = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
