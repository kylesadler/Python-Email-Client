import os
from util import get_logger, render_template, assert_string, assert_string_list, clean_html

logger = get_logger(__name__)

class EmailTemplate:
    """ this class makes it easy to load and render email templates """
    def __init__(self, path, **kwargs):
        """ creates an EmailTemplate
            @input path path to jinja2 template
            @input kwargs any of subject, attachments, to, cc, inline_attachments
                kwargs must contain subject and to in either __init__() or fill()
        """
        self.path = path
        assert os.path.isfile(self.path)

        for field in kwargs:
            assert field in ['subject', 'inline_attachments', 'attachments', 'to', 'cc']

        self.args = kwargs

    def fill(self, template_args, **kwargs):
        """ returns an Email object
            @input template_args dictionary of arguments for template rendering
            @input kwargs any of subject, attachments, to, cc, inline_attachments
                kwargs must contain subject and to in either __init__() or fill()
        """
        for field in kwargs:
            assert field in ['subject', 'inline_attachments', 'attachments', 'to', 'cc']

        args = {**self.args, **kwargs}
        args['html'] = render_template(self.path, template_args)
        args['text'] = clean_html(args['html']).strip() # generate text template from html version

        return Email(**args)

class Email:
    """ class storing all fields needed to send an email with an Gmail object """
    def __init__(self, html, text, subject, to, cc=[], inline_attachments=[], attachments=[]):
        self.html = html
        self.text = text
        self.subject = subject
        self.to = to if isinstance(to, list) else [to] # support both strings and lists of strings
        self.cc = cc if isinstance(cc, list) else [cc]
        self.inline_attachments = inline_attachments
        self.attachments = attachments

        [assert_string(x) for x in [self.html, self.text, self.subject]]
        [assert_string_list(x) for x in [self.to, self.cc, self.inline_attachments, self.attachments]]
            