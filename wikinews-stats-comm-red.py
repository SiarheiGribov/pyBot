#!/usr/bin/env python
# -- coding: utf-8 --

import time
import requests
import login

ua = {"User-agent": "pyBot/wikinews-statpages (toolforge/iluvatarbot; iluvatar@tools.wmflabs.org) requests"}
API_url = "https://ru.wikinews.org/w/api.php"
text_comment = "{{комментарии2}} <!-- Оставьте эту строчку. Пишите комментарий ниже. -->"

try:
    with open("pyBot/wikinews/service/stats-comments-redirects.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        f.close()
    if len(lines) == 2:
        timestamp = str(lines[0]).rstrip("\n")
        page_name = str(lines[1]).rstrip("\n")
except:
    timestamp = "1970-01-01T00:00:01Z"
    page_name = ""


def check_cats(title):
    params = {"action": "raw", "title": title}
    r = requests.get(url=API_url, params=params)
    data = r.text

    if "#REDIRECT" in data or "#перенаправление" in data or "{{перенаправление" in data or "←" in data or \
            "{{Категория для категорий" in data or "{{Категория для категория" in data or "{{Метакатегория" in data or \
            "{{Categoryredirect" in data or "{{Cr" in data or "{{Сategoryredirect" in data or \
            "{{Сategory redirect" in data or "{{Category redirect" in data:
        return False
    else:
        return True


def handler(members, old_title):
    if len(members) > 0:
        if str(members[0]["title"]) != "":
            with open("pyBot/wikinews/service/stats-comments-redirects.txt", "w", encoding="utf-8") as fw:
                fw.write(members[0]["timestamp"] + "\n" + str(members[0]["title"]))
                fw.close()

    params_list = []
    for change in members:
        if str(change["title"]) != old_title:
            title = str(change["title"])
            if not title.replace("Категория:", "").startswith('Викиновости:') \
                    and not title.replace("Категория:", "").startswith("Шаблоны:") \
                    and not title.replace("Категория:", "").startswith("Люди:") \
                    and not title.replace("Категория:", "").startswith("Справка:") \
                    and not title.replace("Категория:", "").startswith("User "):
                if change["ns"] == 0:
                    params_list.append({"action": "edit", "format": "json", "utf8": "1", "createonly": 1, "bot": 1,
                                        "title": "Комментарии:" + title, "text": str(text_comment),
                                        "summary": "Создание страницы комментариев"})
                if change["ns"] == 14 and check_cats(title):
                    params_list.append({"action": "edit", "format": "json", "utf8": "1", "createonly": 1, "bot": 1,
                                        "title": title.replace("Категория:", ""),
                                        "text": "#перенаправление [[" + title + "]]",
                                        "summary": "Создание перенаправления для категории"})
                    params_list.append({"action": "edit", "format": "json", "utf8": "1", "createonly": 1,
                                        "title": "Викиновости:Статистика страниц/" + title,
                                        "text": "{{Статистика страницы|" + title + "}}",
                                        "summary": "Создание страницы статистики"
                                        })
    if len(params_list) > 0:
        token, cookies = login.login(server="ru.wikinews")
        for param in params_list:
            param["token"] = token
            requests.post(url=API_url, data=param, cookies=cookies)
            time.sleep(5)


def get_data():
    try:
        params = {
            "action": "query", "format": "json", "utf8": "1", "list": "recentchanges", "rcend": timestamp,
            "rctype": "new", "rcprop": "title|timestamp", "rcdir": "older", "rcnamespace": "0|14",
            "rcshow": "!redirect", "rclimit": 500
        }
        r = requests.post(url=API_url, data=params, headers=ua).json()["query"]["recentchanges"]
    except:
        time.sleep(30)
        get_data()
    else:
        handler(r, page_name)


get_data()
