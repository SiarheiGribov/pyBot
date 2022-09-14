#!/usr/bin/env python
# -- coding: utf-8 --

import json
import time
import requests
from sseclient import SSEClient as EventSource
import login

token, cookies = login.login(server="ru.wikipedia")

url = 'https://stream.wikimedia.org/v2/stream/revision-create'
API_url = "https://ru.wikinews.org/w/api.php"

def checkCats(title):
    params = {"action": "raw", "title": title}
    r = requests.get(url=url, params=params)
    data = r.text

    if "#REDIRECT" in data or "#перенаправление" in data or "{{перенаправление" in data or "←" in data or "{{Категория для категорий" in data  or "{{Категория для категория" in data or "{{Метакатегория" in data  or "{{Categoryredirect" in data or "{{Cr" in data or "{{Сategoryredirect" in data or "{{Сategory redirect" in data or "{{Category redirect" in data:
        return False
    else:
        return True

def handler(change):
    if change["database"] == "ruwikinews" and "rev_parent_id" not in change and change["page_is_redirect"] == False and not str(change["page_title"]).replace("Категория:", "").startswith('Викиновости:') and not str(change["page_title"]).replace("Категория:", "").startswith("Шаблоны:") and not str(change["page_title"]).replace("Категория:", "").startswith("Люди:") and not str(change["page_title"]).replace("Категория:", "").startswith("Справка:"):
        if change["page_namespace"] == 0 or change["page_namespace"] == 14:
            token, cookies = login.login(server="ru.wikinews")
            params = {"action": "edit", "format": "json", "utf8": "1", "createonly": 1, "bot": 1, "token": token}
            if change["page_namespace"] == 0:
                params["title"] = "Комментарии:" + str(change["page_title"])
                params["text"] = "{{комментарии2}} <!-- Оставьте эту строчку. Пишите комментарий ниже. -->"
                params["summary"] = "Создание страницы комментариев"
            if change["page_namespace"] == 14 and checkCats(str(change["page_title"])):
                params["title"] = str(change["page_title"]).replace("Категория:", "")
                params["text"] = "#перенаправление [[" + str(change["page_title"]) + "]]"
                params["summary"] = "Создание перенаправления для категории"
            requests.post(url=API_url, data=params, cookies=cookies)
            time.sleep(5)


def start():
    try:
        for event in EventSource(url, retry=30000):
            if event.event == 'message':
                try:
                    change = json.loads(event.data)
                except ValueError:
                    pass
                else:
                    handler(change)
    except Exception:
        print("HTTP error")
        time.sleep(30)
        start()


start()
