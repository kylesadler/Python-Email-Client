# set this up on database servers by running crontab -e

SHELL=/bin/bash
MAILTO=kylesadler5@gmail.com
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin

# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed

# send at 8:30am on weekdays
30 8 * * 1 python send.py
30 8 * * 2 python send.py
30 8 * * 3 python send.py
30 8 * * 4 python send.py
30 8 * * 5 python send.py
