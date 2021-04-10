#!/usr/bin/env python3
# coding: utf8

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import datetime as dt
import json
import sys
sys.path.append('pyBot/ext_libs')
import toolforge

conn = toolforge.connect('ruwiki_p')
def get_values(id):
    query = "SELECT substring(rev_timestamp, 1, 8) date_, count(*) AS c FROM revision left join change_tag on rev_id = ct_rev_id WHERE ct_tag_id = " + str(id) + " AND DATE(rev_timestamp) >= DATE(NOW()) - INTERVAL 30 DAY AND DATE(rev_timestamp) < DATE(NOW()) - INTERVAL 0 DAY GROUP BY date_ ORDER BY date_ asc"
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    x = []
    y = []
    for el in result:
        raw = dt.datetime.strptime(dt.datetime.strftime(dt.datetime.strptime(el[0].decode("utf-8"), "%Y%m%d"), "%Y-%m-%d"), "%Y-%m-%d")
        x.append(raw)
        y.append(el[1])
    return x, y

val1 = get_values(94)
val2 = get_values(102)

fig_size = plt.rcParams["figure.figsize"]
fig_size[0] = 20
fig_size[1] = 8
plt.rcParams["figure.figsize"] = fig_size
plt.xlabel("Months")
plt.ylabel("Questions")
plt.title("Questions per day")
plt.plot(val1[0], val1[1], label="Module")
plt.plot(val2[0], val2[1], label="Panel")
plt.gcf().autofmt_xdate()
plt.legend()
plt.savefig("newcomers-30.png")
# plt.show()
