import os
import getpass
import functools
from datetime import datetime
from pprint import pprint, pformat

from pymail import Gmail, EmailTemplate
from pymail.util import get_logger, print_emails
from pymail.util.at_util.clean_parse import clean_html, parse_state
from pymail.util.at_util.db import get_db, get_county_type, all_fields_exist

logger = get_logger(__name__)

testing = False
# testing = True


def main():
    
    username = os.environ.get('ALERT_USERNAME') or input("Enter username: ")
    password = os.environ.get('ALERT_PASSWORD') or getpass.getpass(f'Enter password for {username}: ')

    gmail = Gmail(username, password, testing)
    
    # contacts = [ {
    #     'email': 'grant@acretrader.com',
    #     'name': 'Grant'
    # }]

    contacts = [{
        'email': 'krs028@uark.edu',
        'name' : 'Kyle'
        'subscribed_sites': [
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
    }]

    DATE = datetime.now().strftime("%B %d, %Y")

    scraper_db = MongoDBTunnel(ip, ssh_user, ssh_pkey, ssh_user, ssh_pass)['scraper']

    # FARMS, raw_data = get_farms(scraper_db)

    raw_data = []
    FARMS = []

    for farm in scraper_db.find():
        
        required_fields = ['url', 'state', 'county', 'price', 'acres']
        if not all_fields_exist(required_fields, farm):
            logger.error(f"farm missing one of {required_fields}:\n{pformat(farm)}")
            continue

        # pass over farms older than 1 day
        # note: this won't work because different timezone on db server
        if farm['_id'].generation_time < int(datetime.now().strftime("%s")) - 60*60*24:
            continue

        state = parse_state(farm['state'])

        raw_data.append(farm)
        FARMS.append({
            'title': farm['title'] if 'title' in farm else 'Untitled Listing',
            'url': farm['url'],
            'price': '${:0,.2f}'.format(farm['price']),
            'acres': farm['acres'],
            'location': f'{farm["county"]} {get_county_type(state)}, {state}',
        })


    NUM_FARMS = len(FARMS)

    if NUM_FARMS == 0:
        logger.info('no farms found. Exiting...')
        return

    ALL_LISTINGS_URL = "http://comptool.acretrader.com/listing-alerts"


    template = EmailTemplate(
        os.path.join(os.path.dirname(__file__), 'alert.html'), 
        subject=f"{NUM_FARMS} new Farms! {DATE} Farm Listing Alerts", 
        cc = [username]
    )


    emails = []
    for contact in contacts:
        emails.append(template.fill(
            template_args={
                'NAME': contact['name'],
                'DATE': DATE,
                'FARMS': FARMS,
                'ALL_LISTINGS_URL': ALL_LISTINGS_URL
            },
            to=contact['email']
        ))

    print_emails(emails)

    for i, x in enumerate(gmail.send(emails)):
        if not x:
            logger.error(f'alert not sent to: {emails[i].to}')



if __name__ == '__main__':
    main()
