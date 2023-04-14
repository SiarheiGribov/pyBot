import re
import time
from random import randrange
import requests
import login

SIGN_MENTORS_URL = 'https://ru.wikipedia.org/wiki/MediaWiki:GrowthMentors.json?action=raw'
BL_URL = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Badlist'
REPORT_URL = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Report'
API_URL = 'https://ru.wikipedia.org/w/api.php'
USER_AGENT = {"User-Agent": "IluvatarBot; iluvatar@tools.wmflabs.org; python3.9; requests"}

while True:
    bad_list, users_list, reasons, old_lines = [], [], [], []
    token, cookies = login.login()
    sign_data_mentors = requests.get(SIGN_MENTORS_URL, headers=USER_AGENT).json()["Mentors"]
    # Чёрный список
    bl = requests.get(BL_URL, headers=USER_AGENT).text.splitlines()
    [bad_list.append(re.sub(r'^\*', '', line)) for line in bl if re.match(r'^\*', line)]
    # Список подписей
    sign_list = ["{0} {1}{2}{3}".format("{{Hello}}", "{{subst:Подпись наставника|",
                                        sign_data_mentors[user]["username"], "}}" ) for user in sign_data_mentors
                 if sign_data_mentors[user]["automaticallyAssigned"] is True]
    
    with open('pyBot/wikipedia/service/timeWelcome.txt') as lines:
        line = lines.read().splitlines()
        lines.close()
    timestamp, rc_id = line[0], line[1]

    # Получаем список юзеров из свежих правок
    payload = {'action': 'query', 'format': 'json', 'list': 'recentchanges', 'rcprop': 'user|timestamp|ids',
               'rcshow': '!bot|!anon', 'rctype': 'new|edit', 'rcend': timestamp, 'rclimit': 5000}
    r_changes = requests.post(API_URL, headers=USER_AGENT, data=payload, cookies=cookies).json()
    users = r_changes["query"]["recentchanges"]
    time_file = open("pyBot/wikipedia/service/timeWelcome.txt", "w")
    time_file.write("{0}\n{1}".format(str(users[0]["timestamp"]), str(users[0]["rcid"])))
    time_file.close()

    n = 1
    for user in users:
        if "user" in user:
            if user['user'] not in users_list and int(user["rcid"]) != int(rc_id) and n <= 500:
                users_list.append(user['user'])
                n += 1
    # Проверяем число правок и не заблокирован ли юзер
    payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'users', 'ususers': "|".join(users_list),
               'usprop': 'blockinfo|editcount'}
    r_userinfo = requests.post(API_URL, headers=USER_AGENT, data=payload, cookies=cookies).json()
    for user in r_userinfo["query"]["users"]:
        if ('blockid' not in user) and ('invalid' not in user) and ('missing' not in user):
            if (user['editcount'] > 0) and (user['editcount'] < 25):
                # Проверяем, не была ли у юзера удалена ЛСО
                payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'logevents', 'letype': 'delete',
                           'letitle': 'User talk:' + user['name']}
                r_is_delete = requests.post(API_URL, headers=USER_AGENT, data=payload, cookies=cookies).json()
                if len(r_is_delete["query"]["logevents"]) == 0:
                    # Если имя не заканчивается на бот / bot
                    if not (re.search(r'(бот|bot|Бот)$', user['name'], flags=re.I)):
                        # Публикуем приветствие, если страница ещё не создана. Также проверяем имя на наличие в нём
                        # элементов из чёрного списка и при необходимости публикуем отчёт
                        [reasons.append(re.sub(r'\\', '', bad_word)) for bad_word in
                         bad_list if re.search(r'' + bad_word, user['name'], re.I)]
                        if len(reasons) > 0:
                            pre_pub = '{0}|{1}|{2}{3}'.format("{{Подозрительное имя учётной записи",
                                                              user['name'], ", ".join(reasons), "}}")
                            report = requests.get(REPORT_URL, headers=USER_AGENT).text.splitlines()
                            if pre_pub not in report:
                                [old_lines.append("{0}\n".format(line)) for line in report if not line == "{{/header}}"]
                                report_page = ''.join(map(str, old_lines))
                                report_page = '{0}\n{1}\n{2}'.format("{{/header}}", pre_pub, report_page)
                                payload = {'action': 'edit', 'format': 'json', 'title': 'User:IluvatarBot/Report',
                                           'text': report_page, 'summary': 'Выгрузка отчёта: подозрительный ник',
                                           'utf8': '', 'token': token}
                                r_bad = requests.post(API_URL, data=payload, headers=USER_AGENT, cookies=cookies)

                        random_index = randrange(0, len(sign_list))
                        sign = sign_list[random_index]
                        payload = {'action': 'edit', 'format': 'json', 'title': 'User talk:' + user['name'], 'utf8': '',
                                   'createonly': '1', 'recreate': '0', 'notminor': '', 'text': sign,
                                   'summary': u'Добро пожаловать!', 'token': token}
                        r_edit = requests.post(API_URL, data=payload, headers=USER_AGENT, cookies=cookies)
    time.sleep(60)
