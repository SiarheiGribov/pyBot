#!/usr/bin/env python3
# coding: utf8
import sys
from urllib.request import urlopen
import requests
import time
import login
sys.path.append('pyBot/ext_libs')
import toolforge

URL = 'https://ru.wikipedia.org/w/?action=raw&utf8=1&title=Project:Huggle/Message/daily'
old = urlopen(URL).readline()

actions = {}

conn = toolforge.connect('ruwiki_p')
query = "select group_concat(distinct rev_user_text), count(*) from revision, tag_summary where ts_tags like '%huggle%' and (ts_tags like '%mw-rollback%' or ts_tags like '%mw-undo%') and tag_summary.ts_rev_id=revision.rev_id and rev_timestamp > date_sub(now(), interval 1 day) group by rev_user order by count(*) desc;"
with conn.cursor() as cur:
    cur.execute(query)
    res = cur.fetchall()
if (len(res)>0):
    for result in res:
        if not (result[0] == None):
            actions[result[0].decode("utf-8")] = result[1]
query = "SELECT log_user_text, count(*) FROM logging l WHERE (l.log_type like '%delete%' && l.log_timestamp > date_sub(now(), interval 1 day)&& (l.log_comment like('%[[Project:Huggle|HG]] (%') ))order by count(*) desc;"
with conn.cursor() as cur:
    cur.execute(query)
    res = cur.fetchall()
if (len(res)>0):
    for result in res:
        if not (result[0] == None):
            if (result[0].decode("utf-8") in actions):
                actions[result[0].decode("utf-8")] += result[1]
            else:
                actions[result[0].decode("utf-8")] = result[1]
result_string = ""
if (len(actions)>0):
    actions = sorted(actions.items(), key=lambda  item: item[0])
    i = 0
    for name, numb in actions:
        if (i>3):
            break
        result_string += str(name) + " (" + str(numb) + "), "
        i += 1
else:
    result_string = "—"
result_string = result_string.rstrip(", ") + "."
def send(p):
    req = requests.post('https://ru.wikipedia.org/w/api.php', data=p, cookies=cookies)

if not (old.decode('UTF-8').rstrip('\n') == result_string):
    token, cookies = login.login()
    payload = {'action': 'edit', 'format': 'json', 'title': 'Project:Huggle/Message/daily', 'utf8': '', 'text': result_string,
               'summary': 'Обновление данных', 'token': token}
    count = 0
    try:
        if (count>3):
            print(u"Ошибка при публикации")
            exit()
        send(payload)
    except:
        count += 1
        time.sleep(10)