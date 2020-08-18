import os
import sys
import logging
import smtplib
from email import encoders
from jinja2 import Template
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from .at_util import *


formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s.py %(message)s')

ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)

fh = logging.FileHandler('email_alerts.log')
fh.setFormatter(formatter)
fh.setLevel(logging.WARNING)

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger

logger = get_logger(__name__)

# email_template.py
def read_template(path):
    """ load template from specified path """
    with open(path, 'r', encoding='utf-8') as f:
        return Template(f.read())

def render_template(path, args):
    """ load template from path and return with substituted arguments """
    return read_template(path).render(**args)

def assert_string(an_object):
    assert isinstance(an_object, str), f"{type(an_object)} is not str: {an_object}"

def assert_string_list(an_object):
    assert isinstance(an_object, list), f"{type(an_object)} is not list: {an_object}"
    for s in an_object:
        assert_string(s)

# gmail.py
def to_mimes(attachments):
    """ return a list of email.mime.base.MIMEBase objects for the given attachment paths
        @ input attachments list of paths
    """
    return [to_mime(x) for x in attachments]

def to_mime(path):
    """ return a MIMEBase object from the given filename (which may contain wildcards) """
    filename = os.path.basename(path)
    ext = os.path.splitext(filename)[1]

    with open(path, 'rb') as f:
        mime_img = MIMEImage(f.read())

    mime_img.add_header('Content-ID', '<0>')
    mime.add_header('X-Attachment-Id', '0')
    return mime_img

def connect(username, password):
    try:
        logger.info('connecting to Gmail smtp...')

        smtp = smtplib.SMTP(host='smtp.gmail.com', port=587)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        logger.info('sessfully connected to Gmail')
        return smtp

    except smtplib.SMTPException as e:
        logger.error(f'Could not connect to Gmail:\n{e}')
        raise RuntimeError



def print_emails(emails):
    print(f'\n{"-"*30}\n'.join([email_str(x) for x in emails]))

def email_str(email):
    cc = ', '.join(email.cc)
    to = ', '.join(email.to)
    return f'subject: {email.subject}\nto: {to}\ncc: {cc}\n{email.text}'
