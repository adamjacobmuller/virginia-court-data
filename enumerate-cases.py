import requests
import json
import time
import re
import psycopg2
import sys
import logging
import httplib
import datetime

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

courts_fh = open("courts.json", "r")
courts = json.load(courts_fh)

dates = []

for court in courts:
    for m in xrange(1, 3):
        for d in xrange(1, 31):
            dates.append((2015, m, d, court['fipsCode'], court['name']))

for t_date in dates:
    date = '%02d/%02d/%04d' % (t_date[1], t_date[2], t_date[0])
    pdate = '%04d-%02d-%02d' % (t_date[0], t_date[1], t_date[2])

    try:
        cur.execute("select case_track_id from case_track where fipsCode=%s and date=%s", [t_date[3], pdate])
    except psycopg2.DataError:
        print "ghetto date validation says %s is crazy" % pdate
        conn.rollback()
        continue
    if cur.rowcount == 1:
        print "SKIPPING %s %s" % (t_date[4], pdate)
        continue

    page = 1
    cases = 0
    started = datetime.datetime.now()

    while True:
        data = {
            'curentFipsCode': "%03d" % t_date[3],
            'searchTerm': date,
            'searchFipsCode': "%03d" % t_date[3],
        }
        if page == 1:
            data['caseSearch'] = 'Search'
            if 'caseInfoScrollForward' in data:
                del data['caseInfoScrollForward']
        elif page > 1:
            data['caseInfoScrollForward'] = 'Next'
            if 'caseSearch' in data:
                del data['caseSearch']

        result = requests.post('https://eapps.courts.state.va.us/gdcourts/caseSearch.do', data=data, cookies=cookies)

        print "%s %s %s %s %s" % (t_date[4], result, pdate, page, len(result.text))

        if 'You have exceeded the maximum number of requests allowed for a given time period' in result.text:
            print "> You have exceeded the maximum number of requests allowed for a given time period"
            time.sleep(4)
            continue

        if 'Your previous session has expired due to inactivity' in result.text:
            print "> Your previous session has expired due to inactivity"
            time.sleep(4)
            continue

        g_d = re.findall("displayCaseNumber=([A-Z0-9-]+)&", result.text)

        x = open("raw/html/r-%03d-%s-%s.html" % (t_date[3], pdate, page), "w")
        x.write(result.text.encode("ascii", errors='ignore'))
        x.close()

        x = open("raw/cases-json/r-%03d-%s-%s.json" % (t_date[3], pdate, page), "w")
        json.dump(g_d, x)
        x.close()

        if len(g_d) == 0:
            print "found no more cases on page %d" % page
            break

        for case in g_d:
            cases += 1
            cur.execute("update cases set last=now() where casenumber=%s", [case])
            if cur.rowcount == 0:
                cur.execute("insert into cases (casenumber,fipsCode,first,last) values (%s,%s,now(),now())", [case, t_date[3]])

        conn.commit()

        page += 1
    try:
        cur.execute("insert into case_track (date,fipsCode,started,completed,pages,cases) values (%s,%s,%s,%s,%s,%s)", [
            pdate, t_date[3], started, datetime.datetime.now(), page - 1, cases
        ])
        conn.commit()
    except psycopg2.DataError:
        conn.rollback()
        continue
