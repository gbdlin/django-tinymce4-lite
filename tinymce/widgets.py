# coding: utf-8
"""
TinyMCE 4 forms widget

This TinyMCE widget was copied and extended from this code by John D'Agostino:
http://code.djangoproject.com/wiki/CustomWidgetsTinyMCE
"""

from __future__ import unicode_literals
from __future__ import absolute_import
import sys
import logging
from django.conf import settings
from django.forms import Textarea, Media
from django.forms.widgets import flatatt
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.translation import get_language, get_language_bidi
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.contrib.admin import widgets as admin_widgets
import enchant
import tinymce.settings as mce_settings

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    import simplejson as json
else:
    import json

__all__ = ['TinyMCE']

logging.basicConfig(format='[%(asctime)s] %(module)s: %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(20)


def get_language_config():
    """
    Creates a language configuration for TinyMCE4 based on Django settings

    :return: config
    """
    config = {'language': get_language()[:2]}
    if get_language_bidi():
        config['directionality'] = 'rtl'
    else:
        config['directionality'] = 'ltr'
    if mce_settings.USE_SPELLCHECKER:
        enchant_languages = enchant.list_languages()
        logger.info('Enchant languages: {0}'.format(enchant_languages))
        lang_names = []
        for lang, name in settings.LANGUAGES:
            lang = convert_language_code(lang)
            if lang not in enchant_languages:
                lang = lang[:2]
            if lang not in enchant_languages:
                logger.error('Missing {0} spellchecker dictionary!'.format(lang))
                continue
            if config.get('spellchecker_language') is None:
                config['spellchecker_language'] = lang
            lang_names.append('{0}={1}'.format(name, lang))
        config['spellchecker_languages'] = ','.join(lang_names)
    return config


def convert_language_code(django_lang):
    """
    Converts Django language codes "ll-cc" into ISO codes "ll_CC" or "ll"

    :param django_lang:
    :return: iso_lang
    """
    lang_and_country = django_lang.split('-')
    try:
        return '_'.join((lang_and_country[0], lang_and_country[1].upper()))
    except IndexError:
        return lang_and_country[0]


class TinyMCE(Textarea):
    """
    TinyMCE Widget

    :param attrs:
    :param mce_attrs:
    :param profile:
    """
    def __init__(self, attrs=None, mce_attrs=None, profile=None):
        super(TinyMCE, self).__init__(attrs)
        self.mce_attrs = mce_attrs or {}
        self.profile = get_language_config()
        default_profile = profile or mce_settings.CONFIG
        self.profile.update(default_profile)

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        value = smart_text(value)
        final_attrs = self.build_attrs(attrs)
        final_attrs['name'] = name
        mce_config = self.profile.copy()
        mce_config.update(self.mce_attrs)
        mce_config['selector'] += '#{0}'.format(final_attrs['id'])
        mce_json = json.dumps(mce_config, indent=2)
        if mce_config.get('inline', False):
            html = '<div{0}>{1}</div>\n'.format(flatatt(final_attrs), escape(value))
        else:
            html = '<textarea{0}>{1}</textarea>\n'.format(flatatt(final_attrs), escape(value))
        callbacks = mce_settings.CALLBACKS
        if mce_settings.USE_FILEBROWSER and 'file_browser_callback' not in callbacks:
            callbacks['file_browser_callback'] = 'djangoFileBrowser'
        if mce_settings.USE_SPELLCHECKER and 'spellchecker_callback' not in callbacks:
            callbacks['spellchecker_callback'] = render_to_string('tinymce/spellchecker.js')
        html += '<script type="text/javascript">{0}</script>'.format(
            render_to_string('tinymce/tinymce_init.js',
                             context={'callbacks': callbacks,
                                      'tinymce_config': mce_json[1:-1]})
        )
        return mark_safe(html)

    @property
    def media(self):
        js = [mce_settings.JS_URL]
        if mce_settings.USE_FILEBROWSER:
            js.append(reverse('tinymce-filebrowser'))
        css = {'all': [mce_settings.CSS_URL or reverse('tinymce-css')]}
        return Media(js=js, css=css)


class AdminTinyMCE(TinyMCE, admin_widgets.AdminTextareaWidget):
    pass
