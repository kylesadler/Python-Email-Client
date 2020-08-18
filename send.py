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

# testing = False
testing = True


def get_new_farms(db, query):
    farms = []

    for farm in db.find(query):
        
        # pass over farms older than 1 day
        # note: this won't work because different timezone on db server
        print(farm['_id'].generation_time)
        if farm['_id'].generation_time < int(datetime.now().strftime("%s")) - 60*60*24:
            continue

        required_fields = ['url', 'state', 'county', 'price', 'acres']
        if not all_fields_exist(required_fields, farm):
            logger.error(f"farm missing one of {required_fields}:\n{pformat(farm)}")
            continue

        state = parse_state(farm['state'])

        farms.append({
            'title': farm['title'] if 'title' in farm else 'Untitled Listing',
            'url': farm['url'],
            'price': '${:0,.2f}'.format(farm['price']),
            'acres': farm['acres'],
            'location': f'{farm["county"]} {get_county_type(state)}, {state}',
        })

    return farms


def main():
    
    username = os.environ.get('ALERT_USERNAME') or input("Enter username: ")
    password = os.environ.get('ALERT_PASSWORD') or getpass.getpass(f'Enter password for {username}: ')

    gmail = Gmail(username, password, testing)
    
    contacts = [{
        'email': 'krs028@uark.edu',
        'name' : 'Kyle',
        # 'email': 'grant@acretrader.com',
        # 'name': 'Grant',
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


    scraper_db = MongoDBTunnel(ip, ssh_user, ssh_pkey, ssh_user, ssh_pass)['scraper']
    date = datetime.now().strftime("%B %d, %Y")
    more_listings_url = "http://comptool.acretrader.com/listing-alerts"

    emails = []
    for contact in contacts:
        query = {} # this is personalized
        farms = get_new_farms(scraper_db, query) # TODO fix this

        num_farms = len(farms)

        if num_farms == 0:
            logger.info(f'no farms found for {contact["email"]}. Skipping...')
            continue

        template = EmailTemplate(
            os.path.join(os.path.dirname(__file__), 'alert.html'), 
            subject=f"{num_farms} new Farms! {date} Farm Listing Alerts", 
            cc = [username]
        )

        emails.append(template.fill(
            template_args={
                'NAME': contact['name'],
                'DATE': date,
                'FARMS': farms,
                'URL': more_listings_url
            },
            to=contact['email']
        ))

    print_emails(emails)

    for i, x in enumerate(gmail.send(emails)):
        if not x:
            logger.error(f'alert not sent to: {emails[i].to}')


if __name__ == '__main__':
    main()
