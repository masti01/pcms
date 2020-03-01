#!/usr/bin/python
# -*- coding: utf-8 -*-
"""

call:
    python pwb.py masti/m-check-new-pages.py -ns:0 -newpages -log -pt:0

This is a bot to check new articles:
* if no categories: add {{Dopracowac|kategoria=YYYY-MM}}
* if no wikilinks: add {{Dopracować|linki=YYYY-MM}}
# * if no refs: add {{Dopracować|przypisy=YYYY-MM}}

{{Dopracować}} has to be once per page: combine with already existing

Use global -simulate option for test purposes. No changes to live wiki
will be done.

The following parameters are supported:

&params;

-always           If used, the bot won't ask if it should file the message
                  onto user talk page.

-text:            Use this text to be added; otherwise 'Test' is used

-replace:         Dont add text but replace it

-top              Place additional text on top of the page

-test:            Switch on test prinouts

-summary:         Set the action summary message for the edit.
"""
#
# (C) Pywikibot team, 2006-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id: c1795dd2fb2de670c0b4bddb289ea9d13b1e9b3f $'
#

import pywikibot
from pywikibot import pagegenerators, textlib
from datetime import datetime
import re

from pywikibot.bot import (
    SingleSiteBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)
from pywikibot.tools import issue_deprecation_warning

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class BasicBot(
    # Refer pywikobot.bot for generic bot classes
    SingleSiteBot,  # A bot only working on one site
    # CurrentPageBot,  # Sets 'current_page'. Process it in treat_page method.
    #                  # Not needed here because we have subclasses
    ExistingPageBot,  # CurrentPageBot which only treats existing pages
    NoRedirectPageBot,  # CurrentPageBot which only treats non-redirects
    AutomaticTWSummaryBot,  # Automatically defines summary; needs summary_key
):

    """
    An incomplete sample bot.

    @ivar summary_key: Edit summary message key. The message that should be used
        is placed on /i18n subdirectory. The file containing these messages
        should have the same name as the caller script (i.e. basic.py in this
        case). Use summary_key to set a default edit summary message.
    @type summary_key: str
    """

    summary_key = 'basic-changing'

    def __init__(self, generator, **kwargs):
        """
        Constructor.

        @param generator: the page generator that determines on which pages
            to work
        @type generator: generator
        """
        # Add your own options to the bot and set their defaults
        # -always option is predefined by BaseBot class
        self.availableOptions.update({
            'replace': False,  # delete old text and write the new text
            'summary': None,  # your own bot summary
            'text': 'Test',  # add this text from option. 'Test' is default
            'top': False,  # append text on top of the page
            'test': False, #switch on test functionality
        })

        # call constructor of the super class
        super(BasicBot, self).__init__(site=True, **kwargs)

        # handle old -dry paramter
        self._handle_dry_param(**kwargs)

        # assign the generator to the bot
        self.generator = generator

    def _handle_dry_param(self, **kwargs):
        """
        Read the dry parameter and set the simulate variable instead.

        This is a private method. It prints a deprecation warning for old
        -dry paramter and sets the global simulate variable and informs
        the user about this setting.

        The constuctor of the super class ignores it because it is not
        part of self.availableOptions.

        @note: You should ommit this method in your own application.

        @keyword dry: deprecated option to prevent changes on live wiki.
            Use -simulate instead.
        @type dry: bool
        """
        if 'dry' in kwargs:
            issue_deprecation_warning('dry argument',
                                      'pywikibot.config.simulate', 1)
            # use simulate variable instead
            pywikibot.config.simulate = True
            pywikibot.output('config.simulate was set to True')

    def treat_page(self):
        """Load the given page, do some changes, and save it."""
        refR = re.compile(r'(?P<all><ref.*?<\/ref>)')
        clenaupR = re.compile(r'(?i){{dopracować.*?}}')
        text = self.current_page.text
        links = { 'links' : 0,
                  'cat' : 0,
                  'template' : 0,
                  'infobox' : 0,
                  'refs' : 0,
                  'dopracować' : False }
        cleanupTmpl = False
        summary = []

        if self.current_page.isRedirectPage():
                pywikibot.output(u'Page %s is REDIRECT!' % self.current_page.title())
                return
        elif self.current_page.isDisambig():
                pywikibot.output(u'Page %s is DISAMBIG!' % self.current_page.title())
                return
        else:
            if self.getOption('test'):
                pywikibot.output(u'Title:%s' % self.current_page.title())
                pywikibot.output(u'Depth:%s' % self.current_page.depth)
            for l in self.current_page.linkedPages(namespaces=0):
                if self.getOption('test'):
                    pywikibot.output(u'Links to:[[%s]]' % l.title())
                links['links'] += 1
                #pywikibot.output(u'Links:%s' % len(list(self.current_page.linkedPages(namespaces=0))))
            for t,p in textlib.extract_templates_and_params(text, remove_disabled_parts=True):
                if self.getOption('test'):
                    pywikibot.output('Template:[[%s]]' % t)
                links['template'] += 1
                if 'infobox' in t :
                    links['infobox'] += 1
                if 'Dopracować' in t or 'dopracować' in t :
                    links['dopracować'] = True
                    cleanupTmpl = (t,p)
            for c in textlib.getCategoryLinks(text) :
                if self.getOption('test'):
                    pywikibot.output('Category:%s' % c)
                links['cat'] += 1
            for r in refR.finditer(text):
                if self.getOption('test'):
                    pywikibot.output('Ref:%s' % r.group('all'))
                links['refs'] += 1
            if self.getOption('test'):
                pywikibot.output('Links=%s' % links)
                #pywikibot.output('Cleanup=%s' % re.sub('\n','',textlib.glue_template_and_params(cleanupTmpl)))

        if links['dopracować']:
            if self.getOption('test'):
                pywikibot.output('Cleanup Tmpl FOUND')
        else:
            # add {{Dopracować}}
            t='Dopracować' #template title
            p = {} # template params
            today = datetime.now()
            datestr = today.strftime('%Y-%m')
            if self.getOption('test'):
                pywikibot.output('Date:%s' % datestr)
            if not (links['links'] and links['cat']):
                if not links['links']:
                    p['linki'] = datestr
                    summary.append('linki')
                if not links['cat']:
                    p['kategoria'] = datestr
                    summary.append('kategorie')
                # if not links['refs']:
                #    p['przypisy'] = datestr
                #    summary.append('przypisy')
            cleanupTmpl = (t,p)

            if not p:
                if self.getOption('test'):
                    pywikibot.output('Nothing to add')
                return

            if self.getOption('test'):
                pywikibot.output('Cleanup Tmpl TO ADD')
                pywikibot.output('summary:%s' % summary)
                pywikibot.output('params:%s' % p)
            text = re.sub('\n','',textlib.glue_template_and_params(cleanupTmpl)) + '\n' + text

            # if summary option is None, it takes the default i18n summary from
            # i18n subdirectory with summary_key as summary key.
            self.put_current(text, summary='Sprawdzanie nowych stron, w artykule należy dopracować: %s' % ','.join(summary))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    options = {}
    # Process global arguments to determine desired site
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()

    # Parse command line arguments
    for arg in local_args:

        # Catch the pagegenerators options
        if genFactory.handleArg(arg):
            continue  # nothing to do here

        # Now pick up your own options
        arg, sep, value = arg.partition(':')
        option = arg[1:]
        if option in ('summary', 'text'):
            if not value:
                pywikibot.input('Please enter a value for ' + arg)
            options[option] = value
        # take the remaining options as booleans.
        # You will get a hint if they aren't pre-definded in your bot class
        else:
            options[option] = True

    gen = genFactory.getCombinedGenerator()
    if gen:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        gen = pagegenerators.PreloadingGenerator(gen)
        # pass generator and private options to the bot
        bot = BasicBot(gen, **options)
        bot.run()  # guess what it does
        return True
    else:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False

if __name__ == '__main__':
    main()
