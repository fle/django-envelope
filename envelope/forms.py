# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Contact form class definitions.
"""

import logging
from smtplib import SMTPException

from envelope.settings import ENVELOPE_USE_FLOPPYFORMS

if ENVELOPE_USE_FLOPPYFORMS:
    import floppyforms as forms
else:
    from django import forms

from django.core import mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from envelope import settings
from envelope.signals import after_send


logger = logging.getLogger('envelope.forms')


class ContactForm(forms.Form):
    """
    Base contact form class.

    The following form attributes can be overridden when creating the
    form or in a subclass. If you need more flexibility, you can instead
    override the associated methods such as `get_from_email()` (see below).

    ``subject_intro``
        Prefix used to create the subject line. Default is
        ``settings.ENVELOPE_SUBJECT_INTRO``.

    ``from_email``
        Used in the email from. Defaults to
        ``settings.ENVELOPE_FROM_EMAIL``.

    ``email_recipients``
        List of email addresses to send the email to. Defaults to
        ``settings.ENVELOPE_EMAIL_RECIPIENTS``.

    ``template_name``
        Template used to render the email message. Defaults to
        ``envelope/email_body.txt``.

    """
    sender = forms.CharField(label=_("From"))
    email = forms.EmailField(label=_("Email"))
    subject = forms.CharField(label=_("Subject"), required=False)
    message = forms.CharField(label=_("Message"), widget=forms.Textarea())

    subject_intro = settings.SUBJECT_INTRO
    from_email = settings.FROM_EMAIL
    email_recipients = settings.EMAIL_RECIPIENTS
    template_name = 'envelope/email_body.txt'

    def __init__(self, *args, **kwargs):
        for kwarg in list(kwargs):
            if hasattr(self, kwarg):
                setattr(self, kwarg, kwargs.pop(kwarg))
        super(ContactForm, self).__init__(*args, **kwargs)

    def save(self):
        """
        Sends the message.
        """
        subject = self.get_subject()
        from_email = self.get_from_email()
        email_recipients = self.get_email_recipients()
        context = self.get_context()
        message_body = self.get_message_body()
        try:
            message = mail.EmailMessage(
                subject=subject,
                body=message_body,
                from_email=from_email,
                to=email_recipients,
                headers={
                    'Reply-To': self.cleaned_data['email']
                }
            )
            message.send()
            after_send.send(sender=self.__class__, message=message, form=self)
            logger.info(_("Contact form submitted and sent (from: %s)") %
                        self.cleaned_data['email'])
        except SMTPException:
            logger.exception(_("An error occured while sending the email"))
            return False
        else:
            return True

    def get_context(self):
        """
        Returns context dictionary for the email body template.

        By default, the template has access to all form fields' values
        stored in ``self.cleaned_data``. Override this method to set
        additional template variables.
        """
        return self.cleaned_data.copy()

    def get_subject(self):
        """
        Returns a string to be used as the email subject.

        Override this method to customize the display of the subject.
        """
        return self.subject_intro + self.cleaned_data['subject']

    def get_message_body(self):
        """
        Returns a string to be used as the email body.

        Override this method to customize the display of the body.
        """
        return render_to_string(self.get_template_names(), context)


    def get_from_email(self):
        """
        Returns the from email address.

        Override to customize how the from email address is determined.
        """
        return self.from_email

    def get_email_recipients(self):
        """
        Returns a list of recipients for the message.

        Override to customize how the email recipients are determined.
        """
        return self.email_recipients

    def get_template_names(self):
        """
        Returns a template_name (or list of template_names) to be used
        for the email message.

        Override to use your own method choosing a template name.
        """
        return self.template_name


class ContactFloppyForm(ContactForm):

    class Meta:
        widgets = {
            'sender': forms.TextInput(),
            'email': forms.TextInput(),
            'subject': forms.Select(),
            'message': forms.Textarea(),
        }
