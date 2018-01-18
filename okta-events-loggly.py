#!/usr/bin/env python
#
#

import json
import datetime
import urllib2
import re
import os
import ConfigParser
import lockfile


OKTA_CONFIG="/etc/okta/config"
OKTA_START_TIME="/etc/okta/starttime"
OKTA_LOCK_FILE="/etc/okta/lock"

# lock the script, so that another process cannot run it

def main():
    lock = lockfile.FileLock(OKTA_LOCK_FILE)
    if lock.is_locked() == False:
      try:
          lock.acquire()
          print "OKTA Events Script LOCKED " + str(datetime.datetime.now())
          config = ConfigParser.RawConfigParser()
          config.readfp(open(OKTA_CONFIG))
          org = config.get("Config", "org")
          token = config.get("Config", "token")
          restRecordLimit = config.get("Config", "restRecordLimit")
          runit(org, token, restRecordLimit)
      finally:
          lock.release()
          print "OKTA Events Script UNLOCKED " + str(datetime.datetime.now())


def runit(org, token, restRecordLimit):
    jsonData = getDataFromEndPoint(org, token, getStartTime(), restRecordLimit)
    sendToLoggly(jsonData, restRecordLimit)


def getDataFromEndPoint(org, token, startTime, limit):
    # Since the Okta events cannot have a paging size greater than 1000, this
    # check is set in place to prevent that
    if (int(limit) > 1000):
        limit = '1000'

    url = 'https://' + org + '.okta.com/api/v1/events?startDate=' + startTime + '&limit=' + limit  + '&sortOrder'
    headers = {'Authorization': 'SSWS ' + token}
    request = urllib2.Request(url, None, headers)
    response = urllib2.urlopen(request)
    return json.loads(response.read())

def getStartTime():
    timeFormat = ""
    if os.stat(OKTA_START_TIME).st_size > 0:
      f = open(OKTA_START_TIME)
      t = f.readline().replace(".000Z", "")
      times = datetime.datetime.strptime(t, '%Y-%m-%dT%H:%M:%S')
      timeFormat = getFormattedTime(times.strftime('%Y'), times.strftime('%m'), times.strftime('%d'),
                                    times.strftime('%H'), times.strftime('%M'), times.strftime('%S'))
    else:
      offsetTime = datetime.datetime.now();
      timeFormat = getFormattedTime(offsetTime.strftime('%Y'), offsetTime.strftime('%m'), offsetTime.strftime('%d'),
                                      offsetTime.strftime('%H'), offsetTime.strftime('%M'), offsetTime.strftime('%S'))
    return timeFormat


def getFormattedTime(year, month, day, hour, minute, second):
    return year + "-" + month + "-" + day + "T" + hour + ":" + minute + ":" + second + ".000Z"


def writeOffsetTimeToFile(timeFormat):
    f = open(OKTA_START_TIME, 'w+')
    f.write(timeFormat)
    f.close()

def sendToLoggly(jsonData, restRecordLimit):
    numberOfRows = 0
    lastWrittenPublishedTime = getStartTime()
    fileName = "/var/log/okta-events-" + str(datetime.datetime.date(datetime.datetime.now())) + ".log"
    eventLogFile = open(fileName, 'a')
    logglyToken = "<<loggly_key>>"
    url = "http://logs-01.loggly.com/inputs/{0}/tag/okta-events/".format(logglyToken)
    headers = {"content-type": "text/plain"}
    # this will loop through each of the objects in the JSON list
    for data in jsonData:
        try:
            log_data = json.dumps(data)
            request = urllib2.Request(url, data=log_data, headers=headers)
            f = urllib2.urlopen(request)
            r = f.read()
            lastWrittenPublishedTime = data['published']
        except urllib2.HTTPError, e:
            eventLogFile.write("Loggly service is unavailable: " + lastWrittenPublishedTime + "\n")
            eventLogFile.write("Loggly response code:" + e.code + "\n")
            break
        except Exceptions as e:
            print 'Exception occured:' + str(e)
            break

    # if loggly unavalble next run will pick up logs where it left off
    writeOffsetTimeToFile(lastWrittenPublishedTime)


# start this off
main()
