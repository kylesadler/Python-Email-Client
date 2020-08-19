import os
from .util import get_logger, to_mimes, to_mime, connect
from pprint import pformat
from traceback import format_exc
from .email_template import Email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

logger = get_logger(__name__)

class Gmail:
    """ a wrapper class for sending emails with Gmail """
    def __init__(self, username, password, testing=True):
        self.username = username
        self.smtp = connect(username, password)
        self.testing = testing
        
        if self.testing:
            logger.info('set to TESTING mode')
    
    def send(self, emails):
        if isinstance(emails, list):
            return self._send_many(emails)
        else:
            return self._send_one(emails)

    def _send_many(self, emails):
        sent = [] # boolean list. sent[0] is True if email[0] was sent
        for email in emails:
            sent.append(self._send_one(email))
            if not sent[-1]:
                logger.error(f'error sending {email.subject} to {email.to}')

            if len(sent) % 29 == 0: # max 30 emails per minute
                logger.debug('pausing due to email limits')
                time.sleep(65)
                logger.debug('resuming')

        logger.info(f'done sending: {len(sent)} / {len(emails)} emails.')
        return sent

    def _send_one(self, email):
        """ @input email Email object to be sent 

        The MIME structure should be
            message (mixed)
                body (alternative)
                    text (text)
                    html (related)
                        html (html)
                        inline attachment (image)
                        inline attachment (image)
                        ...
                attachment
                attachment
                ...
        """
        assert isinstance(email, Email), f'email must be Email object: got type {type(email)}'
        
        message = MIMEMultipart()
        message['From'] = self.username
        message['Subject'] = email.subject
        message['To'] = ', '.join(email.to)
        
        if len(email.cc) > 0:
            message['Cc'] = ', '.join(email.cc)
            recepients = [*email.to, *email.cc]
        else:
            recepients = email.to
        
        # create messge body, attaching html last so it shows as default
        message_body = MIMEMultipart('alternative')
        message_body.attach(MIMEText(email.text, "plain"))
        
        # create html body with inline images
        html_body = MIMEMultipart("related")
        html_body.attach(MIMEText(email.html, "html"))
        
        # attach inline images here
        for i, path in enumerate(email.inline_attachments):
            with open(path, 'rb') as f:
                inline_img = MIMEImage(f.read())

            inline_img.add_header('Content-ID', f'<{i}>')
            inline_img.add_header('X-Attachment-Id', f'{i}')
            html_body.attach(inline_img)
        
        message_body.attach(html_body)
        message.attach(message_body)

        # add attachments to message here TODO check this
        for i, path in enumerate(email.attachments):
            filename = os.path.basename(path)
            ext = os.path.splitext(filename)[1]
            with open(path, "rb") as f:
                data = f.read()
            
            if ext == '.png':
                attach = MIMEImage(data)
            elif ext == '.pdf':
                attach = MIMEApplication(data, _subtype="pdf")
            elif ext == '.docx':
                attach = MIMEApplication(data, _subtype ='vnd.openxmlformats-officedocument.wordprocessingml.document')
            else:
                logger.error(f'{filename} not attatched: {ext} files not supported')
                raise RuntimeError
                
            attach.add_header('Content-Disposition', 'attachment', filename=filename)
            
            message.attach(attach)
        

        # logger.debug(f'message:\n{message}')

        if self.testing:
            logger.debug(f'sending TEST {email.subject} to {recepients}')
            logger.info(f'sent TEST email to {recepients}')
        
        else: # send the message
            logger.debug(f'sending {email.subject} to {recepients}')
            
            try:
                failed_recipients = self.smtp.sendmail(message['From'], recepients, message.as_string())
            except smtplib.SMTPException:
                logger.error('email failed for all recipients\n' + format_exc())
                return False

            if bool(failed_recipients): # if exists and non-empty
                succeed_list = [x for x in recepients if x not in list(failed_recipients.keys())]
                logger.info(f'sent email to {succeed_list}')
                logger.warning('failed recipients:\n' + pformat(failed_recipients))

            else:
                logger.info(f'sent email to {recepients}')
        
        return True

    def __del__(self):
        try:
            self.smtp.quit()
        except:
            pass
        logger.info('exiting...')