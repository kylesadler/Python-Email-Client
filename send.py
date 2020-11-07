import os
import json
import urllib3
import getpass
import requests
import functools
from datetime import datetime, timezone, timedelta
from pprint import pprint, pformat

from pymail import Gmail, Outlook, EmailTemplate
from pymail.util import get_logger, print_emails

logger = get_logger(__name__)

TESTING = False
# TESTING = True


def main():
    
    username, gmail = login_gmail()

    template = EmailTemplate(
        os.path.join(os.path.dirname(__file__), 'email.html'), 
        cc = [username],
        template_args={}
    )

    contacts = [
        {
            'email': 'john@fake.edu',
            'name' : 'John',
        }, {
            'email': 'jane@fake.edu',
            'name' : 'Jane',
        }
    ]

    emails = []
    for contact in contacts:
        logger.info(f'emailing {contact["email"]}')
        emails.append(create_email(contact, template))
    
    if TESTING and len(emails) > 0:
        print_emails(emails)

    send_emails(emails, gmail)


def send_emails(emails, gmail):
    for i, x in enumerate(gmail.send(emails)):
        if not x:
            logger.error(f'alert not sent to: {emails[i].to}')


def create_email(contact, template, date, farms):
    return template.fill(
            template_args={
                'NAME': contact['name'],
            },
            to=contact['email'],
            subject=f"A Testing Email"
        )


def login_gmail():
    username = os.environ.get('USERNAME') or input("Enter username: ")
    password = os.environ.get('PASSWORD') or getpass.getpass(f'Enter password for {username}: ')

    return username, Gmail(username, password, TESTING)


if __name__ == '__main__':
    main()
