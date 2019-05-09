#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An incomplete sample script by masti for creating statistics/listings pages

This is not a complete bot; rather, it is a template from which simple
bots can be made. You can rename it to mybot.py, then edit it in
whatever way you want.

Use global -simulate option for test purposes. No changes to live wiki
will be done.

The following parameters are supported:

&params;

-always           If used, the bot won't ask if it should file the message
                  onto user talk page.   

-outpage          Results page; otherwise "Wikipedysta:mastiBot/test" is used

-maxlines         Max number of entries before new subpage is created; default 1000

-text:            Use this text to be added; otherwise 'Test' is used

-replace:         Dont add text but replace it

-top              Place additional text on top of the page

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
from pywikibot import pagegenerators
import re

from pywikibot.bot import (
    MultipleSitesBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)
    #SingleSiteBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)
from pywikibot.tools import issue_deprecation_warning
import datetime

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class BasicBot(
    # Refer pywikobot.bot for generic bot classes
    #SingleSiteBot,  # A bot only working on one site
    MultipleSitesBot,  # A bot only working on one site
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
            'outpage': 'User:mastiBot/test', #default output page
            'maxlines': 1000, #default number of entries per page
            'test' : False,
        })

        # call constructor of the super class
        #super(BasicBot, self).__init__(site=True, **kwargs)
        super(BasicBot, self).__init__(**kwargs)

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

    def run(self):
        """TEST"""
        pywikibot.output(u'THIS IS A RUN METHOD')
        outputpage = self.getOption('outpage')
        pywikibot.output(u'OUTPUTPAGE:%s' % outputpage)
        maxlines = self.getOption('maxlines')
        pywikibot.output(u'MAXLINES:%s' % maxlines)
        for p in self.generator:
            pywikibot.output(u'[%s] Treating: %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),p.title()))
            #pywikibot.output('INTERWIKI:%i' % self.treat(p))
            if not self.treat(p):
                pywikibot.output('NO PL INTERWIKI')

    """ wersja ze stroną pomocniczą
    def treat(self, page):
        results = {} # {lang,catname,{count,listofarticles}}
        lineR = re.compile(ur'(?m)^# \[\[:(?P<lang>.*?):(?P<cat>.*?):(?P<catname>.*?)\]\]')

        for c in re.finditer(lineR,page.text):
            count = 0
            lang = c.group('lang')
            cat = c.group('cat')
            catname = c.group('catname')
            if self.getOption('test'):
                pywikibot.output('l:%s c:%s n:%s' % (lang,cat,catname))

            site = pywikibot.Site(lang,'wikipedia')
            remotepage = pywikibot.Category(site,cat+':'+catname)
            pywikibot.output(remotepage.title(asLink=True))
            artlist = []
            for a in remotepage.articles():
                count += 1
                if self.getOption('test'):
                    pywikibot.output(u'[%s][%i] Treating: %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),count,a.title(asLink=True)))
                if not self.treat_page(a):
                    artlist.append(a.title())
                    if self.getOption('test'):
                        pywikibot.output(u'[%s] appended: %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),a.title(asLink=True)))
            pywikibot.output(u'[%s] Wikipedia: %s, count %i, marked:%i' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),lang,count,len(artlist)))
            results[lang] = {'catname':catname, 'count':count, 'artlist':artlist} 
        if self.getOption('test'):
            pywikibot.output(results)
        return(results)
    """
    # wersja bez strony pomocniczej via interwikidata

    def interwikiGenerator(self,wdpage):
        for i in wdpage['sitelinks']:
            if i.endswith('wiki'):
                lang = i[:-4]
                print lang
                yield pywikibot.Category(pywikibot.Site(lang,'wikipedia'), wdpage['sitelinks'][i])

    def treat(self, page):
        results = {} # {lang,catname,{count,listofarticles}}
        lineR = re.compile(ur'(?m)^# \[\[:(?P<lang>.*?):(?P<cat>.*?):(?P<catname>.*?)\]\]')

        try:
            wd = pywikibot.ItemPage.fromPage(page)
            wdcontent = wd.get()
            pywikibot.output(wdcontent['sitelinks'].keys())
            #return ('plwiki' in wdcontent['sitelinks'].keys())
        except:
            pywikibot.output('WikiData page do not exists')
            return(None)
        for c in self.interwikiGenerator(wdcontent):
            pywikibot.output(c.title())
            lang = c.site.lang

            #if self.getOption('test'):
            #    pywikibot.output('l:%s c:%s n:%s' % (lang,cat,catname))

            artlist = []
            count = 0
            marked = 0
            for a in c.articles():
                count += 1
                if self.getOption('test'):
                    pywikibot.output(u'[%s][%i/%i] Treating: %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),marked,count,a.title(asLink=True,forceInterwiki=True)))
                if not self.treat_page(a):
                    artlist.append(a.title())
                    marked += 1
                    if self.getOption('test'):
                        pywikibot.output(u'[%s] appended: %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),a.title(asLink=True,forceInterwiki=True)))
            pywikibot.output(u'[%s] Wikipedia: %s, count %i, marked:%i' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),lang,count,len(artlist)))
            results[lang] = {'count':count, 'artlist':artlist} 
        if self.getOption('test'):
            pywikibot.output(results)
        return(results)


    def treat_page(self,page):
        """Load the given page, do some changes, and save it."""
        results = {}
        pywikibot.output(u'[%s] Treating: %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),page.title()))
        try:
            wd = pywikibot.ItemPage.fromPage(page)
            wdcontent = wd.get()
            return ('plwiki' in wdcontent['sitelinks'].keys())
        except pywikibot.NoPage:
            return(True)

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
        if option in ('summary', 'text', 'outpage', 'maxlines'):
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
