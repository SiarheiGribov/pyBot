#!/usr/bin/env python
# -- coding: utf-8 --

import time
import requests
import login

wn_API = "https://ru.wikinews.org/w/api.php"
wp_API = "https://ru.wikipedia.org/w/api.php"
ua = {"User-agent": "pyBot/latestnews (toolforge/iluvatarbot; iluvatar@tools.wmflabs.org) requests (python3)"}
token, cookies = login.login(server="ru.wikipedia")

tasks = [
    {"category": "Бизнес", "landing": "Проект:Компании/Викиновости/Бизнес", "count": 20},
    {"category": "Екатеринбург", "landing": "Портал:Екатеринбург/Викиновости", "count": 7},
    {"category": "Казань", "landing": "Портал:Казань/Викиновости", "count": 7},
    {"category": "Музыка", "landing": "Портал:Музыка/Викиновости", "count": 10},
    {"category": "ООН", "landing": "Портал:Организация Объединённых Наций/Викиновости", "count": 10},
    {"category": "Республика Татарстан", "landing": "Портал:Татарстан/Викиновости", "count": 7},
    {"category": "Санкт-Петербург", "landing": "Портал:Санкт-Петербург/Викиновости", "count": 10},
    {"category": "Свердловская область", "landing": "Портал:Свердловская область/Викиновости", "count": 7},
    {"category": "Урал", "landing": "Портал:Урал/Викиновости", "count": 7},
    {"category": "Футбол", "landing": "Портал:Футбол/Викиновости", "count": 10},
    {"category": "Хоккей с шайбой", "landing": "Портал:Хоккей/Викиновости/Хоккей с шайбой", "count": 10},
    {"category": "Экономика", "landing": "Портал:Экономика/Викиновости", "count": 15}
]


def handler(members, task):
    news = []
    i = 0
    for member in members:
        if check(member["title"]):
            i += 1
            news.append("* {{news|" + str(member["title"]) + "}}")
            if i >= task["count"]:
                break
    if len(news) > 0:
        params = {
            "action": "edit", "format": "json", "utf8": "1", "title": str(task["landing"]), "nocreate": 1,
            "text": "\n".join(news), "summary": "Обновление ленты новостей", "token": token
        }
        requests.post(url=wp_API, data=params, cookies=cookies)


def check(page):
    params = {
        "action": "query", "format": "json", "utf8": "1", "prop": "templates", "titles": page, "tlnamespace": 10,
        "tllimit": 500, "tltemplates": "Шаблон:Публиковать"
    }
    res = requests.post(url=wn_API, data=params, headers=ua).json()["query"]["pages"]
    if len(res) > 0:
        n = ""
        for r in res:
            n = r
            break
        if "templates" in res[n]:
            if len(res[n]["templates"]) > 0:
                return True
    return False


def getData(task):
    try:
        params = {
            "action": "query", "format": "json", "utf8": "1", "list": "categorymembers",
            "cmtitle": "Категория:" + str(task["category"]), "cmprop": "timestamp|ids|title", "cmnamespace": 0,
            "cmtype": "page", "cmlimit": 500, "cmsort": "timestamp", "cmdir": "older"
        }
        res = requests.post(url=wn_API, data=params, headers=ua).json()["query"]["categorymembers"]
    except:
        time.sleep(30)
        getData()
    else:
        handler(res, task)


for task in tasks:
    getData(task)
