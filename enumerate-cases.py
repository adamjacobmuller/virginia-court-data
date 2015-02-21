import requests
import json
import time
import re
import psycopg2
import sys
import logging
import httplib

from config import *

if False:
    httplib.HTTPConnection.debuglevel = 1

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


conn = psycopg2.connect(DB_CONNECTION_STRING)
cur = conn.cursor()

dates = [
]

for m in xrange(1, 13):
    for d in xrange(1, 31):
        dates.append((2014, m, d))

for t_date in dates:
    date = '%02d/%02d/%04d' % (t_date[1], t_date[2], t_date[0])
    pdate = '%04d-%02d-%02d' % (t_date[0], t_date[1], t_date[2])

    page = 1

    while True:
        data = {
            'curentFipsCode': '025',
            'searchTerm': date,
            'searchFipsCode': '025',
        }
        if page == 1:
            data['caseSearch'] = 'Search'
            if 'caseInfoScrollForward' in data:
                del data['caseInfoScrollForward']
        elif page > 1:
            data['caseInfoScrollForward'] = 'Next'
            if 'caseSearch' in data:
                del data['caseSearch']

        result = requests.post('https://eapps.courts.state.va.us/gdcourts/caseSearch.do', data = data, cookies = cookies)

        print "%s %s %s %s" % (result, pdate, page, len(result.text))

        if 'You have exceeded the maximum number of requests allowed for a given time period' in result.text:
            print "> You have exceeded the maximum number of requests allowed for a given time period"
            time.sleep(4)
            continue

        if 'Your previous session has expired due to inactivity' in result.text:
            print "> Your previous session has expired due to inactivity"
            time.sleep(4)
            continue

        g_d = re.findall("displayCaseNumber=([A-Z0-9-]+)&", result.text)

        x = open("raw/html/r-%s-%s.html" % (pdate, page), "w")
        x.write(result.text.encode("ascii", errors='ignore'))
        x.close()

        x = open("raw/cases-json/r-%s-%s.json" % (pdate, page), "w")
        json.dump(g_d, x)
        x.close()

        if len(g_d) == 0:
            print "found no more cases on page %d" % page
            break

        for case in g_d:
            cur.execute("update cases set last=now() where casenumber=%s", [case])
            if cur.rowcount == 0:
                cur.execute("insert into cases (casenumber,first,last) values (%s,now(),now())", [case])

        conn.commit()

        page += 1
