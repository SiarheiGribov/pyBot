import re
import time
from random import randrange
import requests
import login

sign_url_mentors = 'https://ru.wikipedia.org/?curid=8409309&action=raw&section=1'
url_bl = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Badlist'
ul_report = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Report'
api_url = 'https://ru.wikipedia.org/w/api.php'
USER_AGENT = {"User-Agent": "IluvatarBot; iluvatar@tools.wmflabs.org; python3.9; requests"}

while True:
    sign_list = []
    token, cookies = login.login()
    sign_data_mentors = requests.get(sign_url_mentors, headers=USER_AGENT).text.splitlines()
    bl = requests.get(url_bl, headers=USER_AGENT).text.splitlines()

    # Список подписей и чёрный список
    for line in sign_data_mentors:
        if re.match(r'^\*\s*?\[\[Участни(?:к|ца):.*?]]\s*?\|.*', line):
            r = re.match(r'^\*\s*?\[\[Участни(?:к|ца):(.*?)]]\s*?\|.*', line)
            if r.group(1) not in sign_list:
                sign_list.append(r.group(1))
    for index, user_name in enumerate(sign_list):
        sign_list[index] = "{0} {1}{2}{3}".format("{{Hello}}", "{{subst:Подпись наставника|", user_name, "}}")
    bad_list = []
    for line in bl:
        if re.match(r'^\*', line):
            bad_list.append(re.sub(r'^\*', '', line))

    with open('pyBot/wikipedia/service/timeWelcome.txt') as lines:
        line = lines.read().splitlines()
        lines.close()
    timestamp, rc_id = line[0], line[1]

    # Получаем список юзеров из свежих правок
    payload = {'action': 'query', 'format': 'json', 'list': 'recentchanges', 'rcprop': 'user|timestamp|ids',
               'rcshow': '!bot|!anon', 'rctype': 'new|edit', 'rcend': timestamp, 'rclimit': 5000}
    r_changes = requests.post(api_url, headers=USER_AGENT, data=payload, cookies=cookies).json()
    users = r_changes["query"]["recentchanges"]
    users_list = []
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
    payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'users', 'ususers':  "|".join(users_list),
               'usprop': 'blockinfo|editcount'}
    r_userinfo = requests.post(api_url, headers=USER_AGENT, data=payload, cookies=cookies).json()
    for user in r_userinfo["query"]["users"]:
        if ('blockid' not in user) and ('invalid' not in user) and ('missing' not in user):
            if (user['editcount'] > 0) and (user['editcount'] < 25):
                # Проверяем, не была ли у юзера удалена ЛСО
                payload = {'action': 'query', 'format': 'json', 'utf8': '', 'list': 'logevents', 'letype': 'delete',
                           'letitle': 'User talk:' + user['name']}
                r_is_delete = requests.post(api_url, headers=USER_AGENT, data=payload, cookies=cookies).json()
                if len(r_is_delete["query"]["logevents"]) == 0:
                    # Если имя не заканчивается на бот / bot
                    if not (re.search(r'(бот|bot|Бот)$', user['name'], flags=re.I)):
                        # Публикуем приветствие, если страница ещё не создана. Также проверяем имя на наличие в нём
                        # элементов из чёрного списка и при необходимости публикуем отчёт
                        reasons, old_lines = [], []

                        for bad_word in bad_list:
                            if re.search(r'' + bad_word, user['name'], re.I):
                                reasons.append(re.sub(r'\\', '', bad_word))
                        if len(reasons) > 0:
                            pre_pub = '{0}|{1}|{2}{3}'.format("{{Подозрительное имя учётной записи",
                                                              user['name'], ", ".join(reasons), "}}")
                            report = requests.get(ul_report, headers=USER_AGENT).text.splitlines()
                            if pre_pub not in report:
                                for line in report:
                                    if not line == '{{/header}}':
                                        old_lines.append("{0}\n".format(line))
                                report_page = ''.join(map(str, old_lines))
                                report_page = '{0}\n{1}\n{2}'.format("{{/header}}", pre_pub, report_page)
                                payload = {'action': 'edit', 'format': 'json', 'title': 'User:IluvatarBot/Report',
                                           'text': report_page, 'summary': 'Выгрузка отчёта: подозрительный ник',
                                           'utf8': '', 'token': token}
                                r_bad = requests.post(api_url, data=payload, headers=USER_AGENT, cookies=cookies)

                        random_index = randrange(0, len(sign_list))
                        sign = sign_list[random_index]
                        payload = {'action': 'edit', 'format': 'json', 'title': 'User talk:' + user['name'], 'utf8': '',
                                   'createonly': '1', 'recreate': '0', 'notminor': '', 'text': sign,
                                   'summary': u'Добро пожаловать!', 'token': token}
                        r_edit = requests.post(api_url, data=payload, headers=USER_AGENT, cookies=cookies)
    time.sleep(60)
