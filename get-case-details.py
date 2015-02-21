import sys
import os
import requests
import logging
import httplib
import json
import re
import psycopg2
import time

from fields import fields
from config import *
from bs4 import BeautifulSoup

conn = psycopg2.connect(DB_CONNECTION_STRING)
cur = conn.cursor()


def clean(string):
    string = string.lower()
    string = string.strip()
    string = re.sub("[^a-z0-9]+", "_", string)
    return string


def clean_things(value):
    if value is None:
        return ''
    value = value.strip()
    value = value.strip(":")
    value = value.strip()
    return value


def parse_stupid_one(table):
    z = list(table)
    r_dict = dict()
    while len(z) > 0:
        key = z.pop(0).string
        value = z.pop(0).string
        if key is None:
            continue
        r_dict[clean_things(key)] = clean_things(value)

    return r_dict

case = None
while True:
    if case is None:
        cur.execute("select casenumber from cases where case_case_number is null limit 1")
        case = cur.fetchone()[0]

    html = "cases/%s.html" % case

    if os.path.exists(html):
        data = open(html).read()
    else:
        url = "https://eapps.courts.state.va.us/gdcourts/caseSearch.do?formAction=caseDetails&displayCaseNumber=%s&&localFipsCode=025&caseActive=true&clientSearchCounter=4" % case
        print url
        response = requests.get(url, cookies = cookies, allow_redirects = False)
        if 'You have exceeded the maximum number of requests allowed for a given time period' in response.text:
            print "> You have exceeded the maximum number of requests allowed for a given time period"
            time.sleep(4)
            continue

        if 'Your previous session has expired due to inactivity' in response.text:
            print "> Your previous session has expired due to inactivity"
            time.sleep(4)
            continue

        print response
        print response.headers['location']
        response = requests.get(response.headers['location'], cookies = cookies)
        print response
        if 'You have exceeded the maximum number of requests allowed for a given time period' in response.text:
            print "> You have exceeded the maximum number of requests allowed for a given time period"
            time.sleep(4)
            continue

        if 'Your previous session has expired due to inactivity' in response.text:
            print "> Your previous session has expired due to inactivity"
            time.sleep(4)
            continue

        cfh = open("cases/%s.html" % case, 'w')
        cfh.write(response.text.encode("ascii", errors='ignore'))
        cfh.close()
        data = response.text

    soup = BeautifulSoup(data)

    x = soup.find_all("form", action="/gdcourts/criminalDetail.do")

    y = x[0].table.find_all("table")

    data = dict()

    for table in y:
        if 'elapsedcollapse' in str(table):
            continue
        if 'Back to Search Results' in str(table):
            continue

        if 'Case Number' in str(table):
            data['case'] = parse_stupid_one(table.find_all("td"))
            #print json.dumps(result, indent = 4)
            continue

        if 'Code Section' in str(table):
            data['charge'] = parse_stupid_one(table.find_all("td"))
            #print json.dumps(result, indent = 4)
            continue

        if 'Final Disposition' in str(table):
            data['disposition'] = parse_stupid_one(table.find_all("td"))
            #print json.dumps(result, indent = 4)
            continue
        #else:
        #    print "--------------------------------------------------------------------------------------"
        #    print table

        #print "--------------------------------------------------------------------------------------"
        #print table

    for data_type in data:
        for l_key in data[data_type]:
            ll_key = "%s_%s" % (data_type, clean(l_key))
            ll_value = data[data_type][l_key]
            if ll_key in fields:
                if 'translator' in fields[ll_key]:
                    ll_value = fields[ll_key]['translator'](data[data_type][l_key])
            if ll_value == '':
                ll_value = None
            cur.execute("update cases set %s=%%s where casenumber=%%s" % ll_key, [ll_value, case])
            print "%s %s" % (ll_key, ll_value)

    cur.execute("update cases set json=%s where casenumber=%s", [json.dumps(data), case])
    conn.commit()
    case = None
