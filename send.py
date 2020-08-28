import os
import getpass
import requests
import functools
from datetime import datetime, timezone, timedelta
from pprint import pprint, pformat

from pymail import Gmail, EmailTemplate
from pymail.util import get_logger, print_emails
from pymail.util.at_util.clean_parse import clean_html, parse_state, get_county_type
from pymail.util.at_util.db import all_fields_exist
from pymail.util.at_util import MongoDBTunnel

logger = get_logger(__name__)

# TESTING = False
TESTING = True


def main():
    
    db = get_remote_db()
    scraper_farms = db['scraper']

    username, gmail = login_gmail()

    get_listings_url = "http://comptool.acretrader.com/listing-alerts"

    post_listings_url = "http://comptool.acretrader.com/api/postAlerts"

    template = EmailTemplate(
        os.path.join(os.path.dirname(__file__), 'alert.html'), 
        cc = [username],
        template_args={ 'URL': get_listings_url }
    )

    alert_sites = [
        'wingertrealty.com',
        'thefarmagency.com',
        'mgw.us.com',
        'bigfarms.com',
        'halderman.com',
        'hagemanrealty.com',
        'prairiefarmland.com',
        'firstmidag.com',
        'kingrealestatear.com',
        'glaubfm.com',
        'schraderauction.com',
        'sterlinglandcompany.com',
        'rutledgeinvestment.com',
        'wellonsland.com',
        'iowafarmlandbroker.com',
        'landprollc.us',
        'roosterag.com'
    ]

    contacts = [{
        'email': 'krs028@uark.edu',
        'name' : 'Kyle',
        # 'email': 'grant@acretrader.com',
        # 'name': 'Grant',
        'alert_sites': alert_sites,
    }]

    # get CST date
    # technically this doesn't account for daylight savings time, but it's probably fine
    current_date = datetime.now(timezone(timedelta(hours=-6))).strftime("%B %d, %Y")
    current_time = datetime.now(timezone.utc) # get UTC timestamp

    emails = []
    for contact in contacts:
        logger.info(f'finding alerts for {contact["email"]}')
        alerts = get_alerts(scraper_farms, current_time, contact['alert_sites'])

        if len(alerts) == 0:
            logger.warning(f'no new alerts found for {contact["email"]}. skipping...')
        else:
            logger.info(f'{len(alerts)} new alerts found for {contact["email"]}')
            post_data(post_listings_url, alerts)
            
            if len(alerts) > 10:
                alerts = alerts[:10]
            
            emails.append(create_email(contact, template, current_date, alerts))
    
    if TESTING and len(emails) > 0:
        print_emails(emails)

    send_emails(emails, gmail)



def post_data(url, alerts):
    """ posts data to url and logs any errors """

    data = {'api_key' : os.environ['ALERT_API_KEY'], 'farms' : alerts}

    response = requests.post(url, data=data)
    if response.status != 200:
        response_dict = { x: getattr(res, x) for x in dir(res) if '_' != x[0] } # all non-private attributes
        logger.error(f'recieved response {pformat(response_dict)}')


def get_query(alert_sites):
    """ given a list of sites, return a mongodb query to find farms from those sites """
    query = { "$or" : [{ "url" : { "$regex": site } } for site in alert_sites] }
    logger.debug(f'querying alerts for {alert_sites}')
    return query


def get_alerts(collection, current_time, alert_sites):
    """ returns a list of dictionaries corresponding to farms scraped less than 1 day before current_time
        collection is open MongoDB collection of farms
        current_time is the current UTC time in a datetime object
        alert_sites is a list of websites to get new farms from
    """
    alerts = []
    required_fields = ['url', 'state', 'county', 'price', 'acres']

    for farm in collection.find(get_query(alert_sites)):
        
        # pass over farms older than 1 day based on 
        if (current_time - farm['_id'].generation_time).days > 0:
            continue
        
        if not all_fields_exist(required_fields, farm):
            logger.error(f"farm missing one of {required_fields}:\n{pformat(farm)}")
            continue

        state = parse_state(farm['state'])
        alerts.append({
            'title': farm['title'] if 'title' in farm else 'Untitled Listing',
            'url': farm['url'],
            'price': '${:0,.2f}'.format(farm['price']),
            'acres': farm['acres'],
            'location': f'{farm["county"]} {get_county_type(state)}, {state}',
        })

    return alerts


def send_emails(emails, gmail):
    for i, x in enumerate(gmail.send(emails)):
        if not x:
            logger.error(f'alert not sent to: {emails[i].to}')


def create_email(contact, template, date, farms):
    return template.fill(
            template_args={
                'NAME': contact['name'],
                'DATE': date,
                'FARMS': farms
            },
            to=contact['email'],
            subject=f"{len(farms)} new Farms! {date} Farm Listing Alerts"
        )


def get_remote_db():
    ip = os.environ['DATABASE_IP']
    ssh_user = os.environ['SSH_USER']
    ssh_pkey = os.environ['SSH_PKEY']
    mongo_user = os.environ['MONGO_USER']
    mongo_pass = os.environ['MONGO_PASS']
    # print(ip, ssh_user, ssh_pkey, mongo_user, mongo_pass)

    db = MongoDBTunnel(ip, ssh_user, ssh_pkey, mongo_user, mongo_pass)
    return db


def login_gmail():
    username = os.environ.get('ALERT_USERNAME') or input("Enter username: ")
    password = os.environ.get('ALERT_PASSWORD') or getpass.getpass(f'Enter password for {username}: ')

    return username, Gmail(username, password, TESTING)


if __name__ == '__main__':
    main()
