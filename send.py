import os
import getpass
from gmail import Gmail
from email_template import EmailTemplate
from pprint import pprint, pformat
from util import get_logger, print_emails
from util.at_util import clean_html, get_db, parse_state, get_county_type, all_fields_exist
from datetime import datetime
import functools

logger = get_logger(__name__)

testing = False
# testing = True

def get_farms(db):
    """ returns formatted farms from database db that are less than 1 day old
        @input db is a MongoDBTunnel object
    """

    output_farms = []
    output = []

    for farm in db.find():
        
        required_fields = ['url', 'state', 'county', 'price', 'acres']
        if not all_fields_exist(required_fields, farm):
            logger.error(f"farm missing one of {required_fields}:\n{pformat(farm)}")
            continue

        # pass over farms older than 1 day
        # note: this won't work because different timezone on db server
        if farm['_id'].generation_time < int(datetime.now().strftime("%s")) - 60*60*24:
            continue

        state = parse_state(farm['state'])

        output_farms.append(farm)
        output.append({
            'title': farm['title'] if 'title' in farm else 'Untitled Listing',
            'url': farm['url'],
            'price': '${:0,.2f}'.format(farm['price']),
            'acres': farm['acres'],
            'location': f'{farm["county"]} {get_county_type(state)}, {state}',
        })
    
    return output, output_farms



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
        'name' : 'Kyle',
    }]

    DATE = datetime.now().strftime("%B %d, %Y")

    update_db = get_db()['scraper']

    FARMS, raw_data = get_farms(update_db)
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
