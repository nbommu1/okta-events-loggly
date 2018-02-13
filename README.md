#Okta Events send to loggly

This Python script will pull Okta events and send to loggly. Run it using a cron job.

##About this Script
- It will bring back at most 1000 entries on each outbound call. 
- There is a system lock on this script when it is initially started to prevent another process from running this script more than once.
- It will record the last published date of the log that it collected (stored in startime) and upon the next time this script is invoked it will retrieve event logs from this published time.
 
# Prerequisites
-	You will need Python 2.7

# Setup
1. Install the prerequisites.
2. Add the necessary okta configuration information inside config.
3. You can omit the contents for "startime". However, if you would like to have this script start collecting events before the current time, you will need to add the following line:
 2017-12-23T19:37:42.000Z  

# Thanks!
inspiration via https://github.com/RobsRepo/Collecting-Okta-Event-Logs

