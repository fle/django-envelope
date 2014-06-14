# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Template tags related to the contact form.
"""

from django import template

from envelope.settings import ENVELOPE_USE_FLOPPYFORMS

try:
    import honeypot
except ImportError:  # pragma: no cover
    honeypot = None


register = template.Library()

if ENVELOPE_USE_FLOPPYFORMS:
    contact_form_tpl = 'envelope/contact_floppy_form.html'
else:
    contact_form_tpl = 'envelope/contact_form.html'


@register.inclusion_tag(contact_form_tpl, takes_context=True)
def render_contact_form(context):
    """
    Renders the contact form which must be in the template context.

    The most common use case for this template tag is to call it in the
    template rendered by :class:`~envelope.views.ContactView`. The template
    tag will then render a sub-template ``envelope/contact_form.html``.
    """
    try:
        form = context['form']
    except KeyError:
        raise template.TemplateSyntaxError("There is no 'form' variable in the template context.")
    return context


@register.simple_tag
def antispam_fields():
    """
    Returns the HTML for any spam filters available.
    """
    content = ''
    if honeypot:
        t = template.Template('{% load honeypot %}{% render_honeypot_field %}')
        content += t.render(template.Context({}))
    return content
