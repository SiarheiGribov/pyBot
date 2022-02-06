import time
import requests
import login

API_url = "https://ru.wikinews.org/w/api.php"
ua = {"User-agent": "pyBot/wikinews-statcats (toolforge/iluvatarbot; iluvatar@tools.wmflabs.org) requests"}

with open("statcats.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()
f.close()
timestamp = str(lines[0])
pageid = str(lines[1])


def getData():
    try:
        params = {
            "action": "query", "format": "json", "utf8": "1", "list": "recentchanges", "rcprop": "timestamp|ids|title",
            "rcnamespace": 14, "rctype": "new", "rclimit": 500, "rcdir": "older", "rcend": timestamp
        }
        r = requests.post(url=API_url, data=params, headers=ua).json()["query"]["recentchanges"]
    except:
        time.sleep(30)
        getData()
    else:
        handler(r, timestamp, pageid)


def handler(members, timestamp, pageid):
    pageid_n = ""
    if len(members) > 0:
        pageid_n = str(members[0]["pageid"])
        timestamp = members[0]["timestamp"]
    token, cookies = login.login(server="ru.wikinews")
    for member in members:
        if str(member["pageid"]) != pageid:
            params = {
                "action": "edit", "format": "json", "utf8": "1",
                "title": "Викиновости:Статистика страниц/" + str(member["title"]),
                "createonly": 1, "text": "{{Статистика страницы|" + str(member["title"] + "}}"),
                "summary": "Создание страницы статистики", "token": token
            }
            requests.post(url=API_url, data=params, cookies=cookies)
    if pageid_n != "":
        with open("statcats.txt", "w", encoding="utf-8") as f:
            f.write(timestamp + "\n" + pageid_n)
        f.close()


getData()
