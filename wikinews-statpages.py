import time
import requests
import login

API_url = "https://ru.wikinews.org/w/api.php"
ua = {"User-agent": "pyBot/wikinews-statpages (toolforge/iluvatarbot; iluvatar@tools.wmflabs.org) requests"}

with open("statpages.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()
f.close()
timestamp = str(lines[0])
pagename = str(lines[1])


# cats (via new pages)

def getData():
    try:
        params = {
            "action": "query", "format": "json", "utf8": "1", "list": "categorymembers",
            "cmtitle": "Категория:Опубликовано", "cmprop": "timestamp|ids|title", "cmnamespace": 0,
            "cmtype": "page", "cmlimit": 500, "cmsort": "timestamp", "cmdir": "older", "cmend": timestamp
        }
        r = requests.post(url=API_url, data=params, headers=ua).json()["query"]["categorymembers"]
    except:
        time.sleep(30)
        getData()
    else:
        handler(r, timestamp, pagename)


def handler(members, timestamp, pagename):
    pagename_n = ""
    if len(members) > 0:
        pagename_n = str(members[0]["title"])
        timestamp = members[0]["timestamp"]
    token, cookies = login.login(server="ru.wikinews")
    for member in members:
        if str(member["title"]) != pagename:
            params = {
                "action": "edit", "format": "json", "utf8": "1",
                "title": "Викиновости:Статистика страниц/" + str(member["title"]),
                "createonly": 1, "text": "{{Статистика страницы|" + str(member["title"] + "}}"),
                "summary": "Создание страницы статистики", "token": token
            }
            requests.post(url=API_url, data=params, cookies=cookies)
    if pagename_n != "":
        with open("statpages.txt", "w", encoding="utf-8") as f:
            f.write(timestamp + "\n" + pagename_n)
        f.close()


getData()
