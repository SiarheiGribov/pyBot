# coding: utf8

import sys
# -*- coding: utf-8 -*-import sys

import sys
sys.path.append("C:\Users\Siarhei\Documents\pywikibot\ext_libs")
import re
import ast
import json
import time
import login
import requests
from urllib2 import urlopen
from bs4 import BeautifulSoup
from sseclient import SSEClient as EventSource
reload(sys)
sys.setdefaultencoding('utf8')

days_history = 5


URL_BL = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Badlinks/links'
attempt = 0
get_complete = False
while get_complete == False:
    try:
        bl = urlopen(URL_BL).readlines()
        get_complete = True
    except:
        attempt += 1
        if attempt == 10:
            print(u"Ошибка при получении чёрного списка ссылок")
            sys.exit()
        time.sleep(300)


url = 'https://stream.wikimedia.org/v2/stream/recentchange'
for event in EventSource(url):
    if event.event == 'message':
        try:
            change = json.loads(event.data)
        except ValueError:
            pass
        else:
            if ('{wiki}'.format(**change)=="ruwiki") and (('{type}'.format(**change)=="edit") or ('{type}'.format(**change)=="new")) and ('{bot}'.format(**change)=="False") and ('{namespace}'.format(**change)=="0"):
                revision=ast.literal_eval('{revision}'.format(**change))
                new_id = str('{new}'.format(**revision))
                res = 0
                diff = ""
                if '{type}'.format(**change)=="new":
                    URL_DIFF = "https://ru.wikipedia.org/w/api.php?action=query&titles=" + str('{title}'.format(**change)) + "&prop=extlinks&format=json&ellimit=500"
                    try:
                        diff = requests.post(URL_DIFF).text
                        old_id = 0
                    except:
                        continue
                else:
                    old_id = str('{old}'.format(**revision))
                    URL_DIFF = "https://ru.wikipedia.org/w/api.php?action=compare&format=json&prop=diff&utf8=1&fromrev=" + old_id + "&torev=" + new_id
                    try:
                        diff_parsed = requests.post(URL_DIFF).json()
                    except:
                        continue
                    for changeDiff in BeautifulSoup(diff_parsed['compare']['*'], "html.parser").findAll("ins", {"class": "diffchange diffchange-inline"}):
                        diff += str(changeDiff) + "\n"
                    for diffAdd in BeautifulSoup(diff_parsed['compare']['*'], "html.parser").findAll("tr"):
                        if not "diffchange diffchange-inline" in str(diffAdd) and not "diff-deletedline" in str(diffAdd):
                            for diffAdd2 in BeautifulSoup(str(diffAdd), "html.parser").findAll("", {"class": "diff-addedline"}):
                                diff += str(diffAdd2) + "\n"

                for i in bl:
                    if re.search(r'' + i.decode('UTF-8').rstrip('\n'), diff):
                        if res == 0:
                            res = str(i.decode('UTF-8').rstrip('\n'))
                        else:
                            res += ", " + str(i.decode('UTF-8').rstrip('\n'))


                if not res==0:
                    prePub = "{{User:IluvatarBot/Подозрительный источник|" + str('{title}'.format(**change)) + "|" + str(old_id) + "|" + str(new_id) + "|" + str(res) + "|" + str(int(time.time())) + "}}" + "\n"
                    token, cookies = login.login()
                    time.sleep(1)
                    raportPage_URL = "https://ru.wikipedia.org/w/?action=raw&utf8=1&title=User:IluvatarBot/Badlinks/raport"
                    try:
                        raport_page = urlopen(raportPage_URL).readlines()
                    except:
                        print("Error during get raport_page.")
                        continue
                    new_pub = []
                    for line in raport_page: # удаляем устаревшие шаблоны
                        timeReg = re.findall(r"(\d*)?\}\}", line.decode("utf-8").strip('\r\n'), re.U | re.I)
                        if not len(timeReg) > 0:
                            print("Timestamp error: " + u"один из шаблонов на странице не имеет отметки времени.")
                            sys.exit()
                        timePast = int(time.time()) - int(timeReg[0])
                        hoursPast = int(days_history) * 24 * 60 * 60
                        if not timePast >= int(hoursPast):
                            new_pub.append(line)
                        raport_page = ''.join(map(str,new_pub))
                    raport_page = prePub + raport_page
                    payload = {'action': 'edit', 'format': 'json', 'title': 'User:IluvatarBot/Badlinks/raport', 'utf8': '', 'text': raport_page, 'summary': 'Выгрузка отчёта: сомнительные источники', 'token': token}
                    time.sleep(1)
                    try:
                        req = requests.post('https://ru.wikipedia.org/w/api.php', data=payload, cookies=cookies)
                    except:
                        print("Error during get publishing.")
                        continue