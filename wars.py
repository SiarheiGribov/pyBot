#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import re
import time
import urllib.parse as quote
from datetime import datetime, timedelta
import threading
import requests
from sseclient import SSEClient as EventSource

LIMIT = 3  # кол-во откатов на проект, порог оповещения
MINUTES = 30  # кол-во минут отсутствия оповещений из проекта от последнего оповещения
PAGE_SIZE = 2500  # предполагаемый вес в байтах спам-страницы


class Edit:
    edits_count = 0

    def __init__(self, domain, database, title, page_id, rev_id, parent_id, next_id, next_user, user, new_len,
                 event_type, timestamp):
        self.domain = domain
        self.wiki = database
        self.title = title
        self.page_id = page_id
        self.rev_id = rev_id
        self.next_id = next_id
        self.user = user
        self.parent_id = parent_id
        self.next_user = next_user
        self.new_len = new_len
        self.type = event_type
        self.timestamp = timestamp
        self.reported = 0
        Edit.edits_count += 1

    def get_url(self, target_type):
        if target_type == "page":
            return "https://{0}/wiki/{1}?action=history&uselang=en".format(
                self.domain, quote.quote_plus(self.title.replace(" ", "_")))
        if target_type == "user":
            return "https://{0}/wiki/Special:Contribs/{1}?uselang=en".format(
                self.domain, quote.quote_plus(self.user.replace(" ", "_")))
        if target_type == "other":
            return "https://{0}/wiki/Special:RecentChanges?uselang=en".format(self.domain)


WIKI_SET = []
DELETE_SUMMARY = ["Requesting [[WP:CSD|speedy deletion]]", "Requesting deletion", "Zahtjev za brisanjem stranice",
                  "দ্রুত অপসারণের জন্য প্রস্তাব করা হল", "Marcant la pàgina per a la seva supressió immediata",
                  "Requesting [[COM:CSD|speedy deletion]]", "Der Artikel wurde zur Schnelllöschung vorgeschlagen",
                  "Αίτημα [[ΒΠ:ΓΔ|άμεσης διαγραφής]]", "Solicitando borrado rápido",
                  "Merkitty poistettavaksi välittömästi", "Demande de [[WP:CSI|suppression immédiate]]",
                  "પાનું હટાવવા વિનંતી", "शीघ्र हटाने का नामांकन", "Meminta [[WP:KPC|penghapusan cepat]]",
                  "Requesting [[Wikipedia:Viðmið um eyðingu greina|speedy deletion]]",
                  "Requesting [[Project:Deletion|speedy deletion]]", "Requesting [[WM:CSD|speedy deletion]]",
                  "Ber om [[WP:HS|hurtigsletting]]", "Requestin delytion", "Requesting [[WP:QD|quick deletion]]",
                  "Номінація статті на [[Вікіпедія:Критерії швидкого вилучення|швидке вилучення]]", "提报快速删除",
                  "Yêu cầu [[WP:CSD|xoá nhanh]]", "Requesting speedy deletion"]
DELETE_SUMMARY_STRICT = ["Smazat", "Leschotrog", "Löschantrag", "Nuweg", "КБУ", "+delete", "+ delete"]
STREAM_URL = 'https://stream.wikimedia.org/v2/stream/mediawiki.revision-tags-change,mediawiki.revision-create'
USER_AGENT = {"User-Agent": "Iluvatar@toolforge; python; requests"}
with open(os.path.dirname(os.getcwd()) + "/swviewer/security/bottoken.ini") as lines:
    lines = lines.read().splitlines()
DISCORD_URL = "https://discord.com/api/webhooks/{0}".format(lines[4].replace("discordwh = ", ""))
GLOBAL_GROUPS = []
storage = []


# Форматирование оповещения
def prepare(arr):
    # Определяем логику оповещения. Если правки одного юзера, то ссылка на вклад юзера.
    # Если правки разных юзеров на одной странице, ссылка на историю страницы.
    # Если ни то, ни дугое, ссылка на свежие правки.
    users, pages = [], []
    for index, el in enumerate(arr):
        arr[index].reported = True
        if el.user not in users:
            users.append(el.user)
        if el.title not in pages:
            pages.append(el.title)
    if len(pages) == 1:
        descr = "Page:\t{0}.".format(pages[0].replace("_", " "))
        return descr, arr[0].get_url("page")
    else:
        if len(users) == 1:
            descr = "User:\t{0}.".format(users[0].replace("_", " "))
            return descr, arr[0].get_url("user")
        else:
            descr = "Users:\t{0};\nPages:\t{1}.".format(", ".join(users).replace("_", " "),
                                                        ", ".join(pages).replace("_", " "))
            return descr, arr[0].get_url("other")


# Сравнение двух таймстампов за вычетом определённого кол-ва минут (для проверки просрочки).
def timestamp_eq(timestamp_now, timestamp_rev, minutes):
    timestamp_now = datetime.strptime(timestamp_now, '%Y-%m-%dT%H:%M:%S%z') - timedelta(minutes=minutes)
    return False if timestamp_now > datetime.strptime(timestamp_rev, '%Y-%m-%dT%H:%M:%S%z') else True


# Пытаемся получить предыдущего юзера и id ревизии
# Если кто-то успел совершить новую правку за 25 секунд, определится неверно.
def get_next_user(domain, page_id, title, timestamp_stream, timestamp):
    next_user = next_parent_id = next_rev_id = -1
    for act in ["mw-rollback", "mw-manual-revert", "mw-undo"]:
        data = {
            "action": "query", "prop": "revisions", "titles": title, "rvlimit": 10, "rvprop": "user|ids",
            "rvstart": timestamp_stream, "rvend": timestamp, "rvtag": act, "format": "json", "utf8": 1
        }
        try:
            next_user_raw = requests.post("https://{0}/w/api.php".format(domain), data=data, headers=USER_AGENT).json()
            next_user = next_user_raw["query"]["pages"][str(page_id)]["revisions"][0]["user"]
            next_parent_id = next_user_raw["query"]["pages"][str(page_id)]["revisions"][0]["parentid"]
            next_rev_id = next_user_raw["query"]["pages"][str(page_id)]["revisions"][0]["revid"]
        except Exception as e:
            if str(e) != "'revisions'":
                print("Get next user error: {0}".format(e))
            pass
        else:
            break
    return next_user, next_parent_id, next_rev_id


# Берём флаги участника
def get_next_user_groups(domain, user):
    if re.search("^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$", user, re.I) or ":" in user:
        return []
    data = {"action": "query", "list": "users", "ususers": user, "usprop": "groups", "format": "json", "utf8": 1}
    try:
        r = requests.post("https://{0}/w/api.php".format(domain), data=data, headers=USER_AGENT).json()
        next_user_groups = r["query"]["users"][0]["groups"]
    except Exception as e:
        print("Get groups error: {0}".format(e))
        return []
    else:
        return next_user_groups


# Оповещаем если накопилось более 3 правок и о вики в последний час не оповещалось.
def report(wiki):
    # Считаем кол-во накапавших откатов в проекте.
    edits_rep = [x for x in storage if x.wiki == wiki]
    # Если среди них есть уже отрепорченные (X минут с которых соответственно не прошло), то игнорим всё (проект).
    wiki_reported = len([y for y in edits_rep if y.reported])
    if len(edits_rep) >= LIMIT and wiki_reported == 0:
        descr, url_target = prepare(edits_rep)
        data = {"content": "", "tts": False, "embeds": [
            {"type": "rich", "title": wiki.upper(), "description": descr, "color": 0xff0008, "url": url_target}]}
        requests.post(DISCORD_URL, json=data)


# Проверка тегов в правке
def check_tags(change, tag):
    if "tags" in change and tag not in change["tags"]:
        return False
    # Если в предыдущей версии не было тега отката, значит был добавлен именно он.
    return True if "prior_state" not in change or "tags" not in change["prior_state"] or \
                   tag not in change["prior_state"]["tags"] else False


def new_handler(change):
    if change["database"] not in WIKI_SET:
        return
    if change["performer"]["user_is_bot"] or ("user_is_bot" in change["performer"]
                                              and change["performer"]["user_is_bot"]) \
            or change["performer"]["user_text"] in GLOBAL_GROUPS:
        return
    if change["page_is_redirect"]:
        return
    if "user_edit_count" in change["performer"] and change["performer"]["user_edit_count"] > 2:
        return
    # Проверка на пространства имён (ЛС и основное), длину станицы в байтах и отсутствие тегов минимального оформления
    if change["page_namespace"] == 2 or \
            (change["page_namespace"] == 0 and "rev_len" in change and change["rev_len"] > PAGE_SIZE):
        # Проверка, не является ли страница в ЛП подстраницей
        if change["page_namespace"] == 2 and change["performer"]["user_text"].replace(" ", "_") \
                + "/" in change["page_title"]:
            return
        elements = ["]]", "}}", "<ref"]
        try:
            url_check_els = "https://{0}/wiki/{1}?action=raw".format(change["meta"]["domain"],
                                                                     quote.quote_plus(change["page_title"]))
            text_check_els = requests.get(url_check_els).text
            if len([el for el in elements if el in text_check_els]) > 0:
                return
        except Exception as e:
            print("Get check elements text error: {0}".format(e))
            return
        # Проверка на наличие внешних ссылок на странице (минимум 1)
        try:
            data = {
                "action": "query", "prop": "extlinks", "titles": change["page_title"], "ellimit": 10, "format": "json",
                "utf8": 1
            }
            ext_check = requests.post("https://{0}/w/api.php".format(change["meta"]["domain"]),
                                      data=data, headers=USER_AGENT).json()
            if "extlinks" not in ext_check["query"]["pages"][str(change["page_id"])]:
                return
            if len(ext_check["query"]["pages"][str(change["page_id"])]["extlinks"]) == 0:
                return
        except Exception as e:
            print("Get external links error: {0}".format(e))
            return
        prefix_title = "Page" if change["page_namespace"] == 0 else "Userpage"
        data = {"content": "", "tts": False, "embeds": [
            {"type": "rich", "title": change["database"].upper(), "description":
                "New {0} by newbie\n{1}:\t{2}.".format(prefix_title.lower(), prefix_title,
                                                       change["page_title"]), "color": 0xff0008,
             "url": "https://{0}/wiki/{1}?uselang=en".format(change["meta"]["domain"],
                                                             quote.quote_plus(change["page_title"]))}]}
        requests.post(DISCORD_URL, json=data)


# Обработчик событий стриме revision-create для поиска КБУ
def delete_handler(change):
    if change["database"] not in WIKI_SET or change["performer"]["user_text"] in GLOBAL_GROUPS:
        return
    # Проверяем комментарий к правке и ищем КБУ для оповещения
    if "comment" in change:
        if change["comment"].lower() in (comm.lower() for comm in DELETE_SUMMARY_STRICT) \
                or len([ds for ds in DELETE_SUMMARY if ds.lower() in change["comment"].lower()]) > 0:
            if "tags" not in change or change["tags"] != "mw-reverted":
                # Обработчик в случае нахождения КБУ. Оповещение.
                data = {"content": "", "tts": False, "embeds": [
                    {"type": "rich", "title": change["database"].upper(), "description":
                        "Possible SD request\nPage:\t{0}.".format(change["page_title"].replace("_", " ")),
                     "color": 0xff0008, "url": "https://{0}/wiki/{1}?uselang=en"
                        .format(change["meta"]["domain"], quote.quote_plus(change["page_title"]))}]}
                requests.post(DISCORD_URL, json=data)


# Обработчик событий стрима tags-change для поиска откатов
def revert_handler(change):
    # Проверяем принадлежность проекта к списку проектов с малым кол-вом админов
    if change["database"] not in WIKI_SET:
        return
    # Проверяем, есть ли вообще теги у правки и наличие тега откаченой правки
    if not check_tags(change, "mw-reverted"):
        return
    # Проверка разницы между временем правки и временем нахлобучивания тега: для предотвр. сраб. на «чистку» проекта
    if not timestamp_eq(change["meta"]["dt"], change["rev_timestamp"], 100):
        return
    # Получаем предыдущего юзера, id правки и пытаемся проверить, не себя ли откатил юзер
    # и не является ли он глоб. или лок. админом.
    # Пред.юзер, пред. правка для более новой правки с тегом отката и id новой правки.
    next_user, next_parent_id, next_id = get_next_user(change["meta"]["domain"],
                                                       change["page_id"], change["page_title"],
                                                       change["meta"]["dt"], change["rev_timestamp"])
    if next_user != -1:
        groups = get_next_user_groups(change["meta"]["domain"], next_user)
        if change["performer"]["user_is_bot"] or ("user_is_bot" in change["performer"]
                                                  and change["performer"]["user_is_bot"]) \
                or "sysop" in groups or next_user in GLOBAL_GROUPS:
            return
        if next_parent_id != -1:
            # Если предыдущ. правка у новой правки с тегом отката равна нашей текущей, равны юзеры, значит это
            # скорее всего откат юзером своей правки.
            if next_parent_id == change["rev_id"] and next_user == change["performer"]["user_text"]:
                return
    rev_parent_id = -1 if "rev_parent_id" not in change else change["rev_parent_id"]
    # Если есть проекты с той же предполагаемой следующей правкой с тегом отката, можем сделать предположение, что это
    # быстрый октат нескольких правок и не включаем в массив новую правку (достаточно 1-й на каждый из откатов).
    if len([x for x in storage if x.next_id == next_id and next_id != -1 and x.wiki == change["database"]]) > 0:
        return
    # Если в массиве есть уже отрепорченные правки из проекта (соответственно, X мин не прошло)
    if len([x for x in storage if x.wiki == change["database"] and x.reported]) > 0:
        return
    storage.append(Edit(change["meta"]["domain"], change["database"], change["page_title"], change["page_id"],
                        change["rev_id"], rev_parent_id, next_id, next_user, change["performer"]["user_text"],
                        change["rev_len"], "revert", time.time()))
    report(change["database"])


# Убираем правки из массива, которым более часа
def outdated():
    for index, item in enumerate(storage):
        if (time.time() - item.timestamp) >= MINUTES * 60:
            del storage[index]
    threading.Timer(float(MINUTES * 60), outdated).start()


def update_wikiset():
    # Создание и обновление списка проектов
    try:
        file_active_sysops = open(os.path.dirname(os.getcwd()) + "/swviewer/public_html/lists/active_sysops.json")
        active_sysops = json.loads(file_active_sysops.read())
        file_active_sysops.close()
        wiki_set_raw = [active_sysop for active_sysop in active_sysops if active_sysops[active_sysop][1] <= 1]
        if len(wiki_set_raw) > 10:
            global WIKI_SET
            WIKI_SET = wiki_set_raw
        if not streams.is_alive():
            streams.start()
    except Exception as active_sysops_error:
        print("Load active sysops list: {0}. Closed.".format(active_sysops_error))
        time.sleep(120)
        update_wikiset()
    time.sleep(86400)
    update_wikiset()


def main():
    try:
        for event in EventSource(STREAM_URL, retry=30000):
            if event.event == 'message':
                try:
                    e = json.loads(event.data)
                except ValueError:
                    pass
                else:
                    if e["meta"]["stream"] == "mediawiki.revision-tags-change":
                        revert_handler(e)
                    else:
                        delete_handler(e) if "rev_parent_id" in e else new_handler(e)
    except Exception as e:
        print("Stream error: {0}".format(e))
        time.sleep(30)
        main()


def start():
    # Загрузка списка стюардов и глобальных администраторов
    try:
        data = {
            "action": "query", "list": "globalallusers", "agulimit": 500, "agugroup": "steward|global-sysop",
            "format": "json", "utf8": 1
        }
        global_groups_r = requests.post(url="https://meta.wikimedia.org/w/api.php", data=data,
                                        headers=USER_AGENT).json()
        global GLOBAL_GROUPS
        GLOBAL_GROUPS = [s["name"] for s in global_groups_r["query"]["globalallusers"]]
    except Exception as e:
        print("Start error: {0}".format(e))
        time.sleep(120)
        start()
    else:
        # Запуск потоков с обновлением списка проектов и очистки просроченных событий
        threading.Thread(target=update_wikiset, name="update").start()
        threading.Thread(target=outdated, name="clr_outdated").start()


streams = threading.Thread(target=main, name="streams")
start()
