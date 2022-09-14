# -- coding: utf-8 --

import re
import login
import requests
from datetime import datetime

ua = {"User-agent": "pyBot/feed (toolforge/iluvatarbot; iluvatar@tools.wmflabs.org) requests"}
months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября",
          "декабря"]
today = datetime.utcnow()
header = "Лента новостей " + re.sub("^0", "", today.strftime("%d")) + " " + months[
    int(today.strftime("%m")) - 1] + " " + today.strftime("%Y") + " года"
content = """{{ЛНН|$3-$2-$1}}

* Пишите тут.

{{ЛНКК|$3-$2-$1}}

{{Категории|}}""".replace("$1", today.strftime("%d")).replace("$2", today.strftime("%m")) \
    .replace("$3", today.strftime("%Y"))
token, cookies = login.login(server="ru.wikinews")
params = {
    "action": "edit", "format": "json", "utf8": "1", "title": header, "text": content, "createonly": 1, "bot": 1,
    "summary": "Создание заготовки ленты новостей", "token": token
}
requests.post(url="https://ru.wikinews.org/w/api.php", data=params, cookies=cookies)
