#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An incomplete sample script by masti for creating statistics/listings pages
Creates a list of articles from featured list
Call:
    python pwb.py masti/ms-featured.py -page:"Kategoria:Artykuły na medal" -outpage:"Wikipedia:Brakujące artykuły na medal z innych Wikipedii" -summary:"Bot aktualizuje listę"
    python pwb.py masti/ms-featured.py -page:"Kategoria:Dobre artykuły" -good -outpage:"Wikipedia:Brakujące dobre artykuły z innych Wikipedii" -summary:"Bot aktualizuje listę"
    python pwb.py masti/ms-featured.py -page:"Kategoria:Listy na medal" -lists -outpage:"Wikipedia:Brakujące listy na medal z innych Wikipedii" -summary:"Bot aktualizuje listę"

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

-negative:        mark if text not in page
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
import datetime
import re

from pywikibot.bot import (
    MultipleSitesBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)
from pywikibot.tools import issue_deprecation_warning

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class BasicBot(
    # Refer pywikobot.bot for generic bot classes
    #SingleSiteBot,  # A bot only working on one site
    MultipleSitesBot,  # A bot working on multiple sites
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
            'outpage': u'User:mastiBot/test', #default output page
            'maxlines': 1000, #default number of entries per page
            'test': False, # print testoutput
            'test2': False, # print testoutput
            'test3': False, # print testoutput
            'test4': False, # print testoutput
            'test5': False, # print testoutput
            'negative': False, #if True negate behavior i.e. mark pages that DO NOT contain search string
            'good': False, # work on good articles
            'lists': False, # work on featured lists

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
        result = {}

        outputpage = self.getOption('outpage')
        #pywikibot.output(u'OUTPUTPAGE:%s' % outputpage)
        for p in self.generator:
            if self.getOption('test'):
                pywikibot.output(u'Treating: %s' % p.title())
            result = self.treat(p)

        header = u'{{Wikipedia:Brakujące artykuły/Nagłówek}}\n\n'
        if self.getOption('good'):
            header += 'Dobre Artykuły'
        elif self.getOption('lists'):
            header += 'Listy na Medal'
        else:
            header += 'Artykuły na Medal'

        header += ' w innych Wikipediach, które nie mają odpowiednika w polskiej Wikipedii\n\n'
        header += 'Ta strona jest okresowo uaktualniana przez [[Wikipedysta:MastiBot|bota]].\n\n'
        header += "Ostatnia aktualizacja: '''" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S (CEST)") +"'''.\n\n"
        header += 'Wszelkie uwagi proszę zgłaszać w [[Dyskusja_Wikipedysty:Masti|dyskusji operatora]].\n\n'
        footer = u''

        self.generateresultspage(result,self.getOption('outpage'),header,footer)
        return

    def generateresultspage(self, redirlist, pagename, header, footer):
        """
        Generates results page from redirlist
        Starting with header, ending with footer
        Output page is pagename
        """
        finalpage = header
        res = sorted(redirlist.keys())
        itemcount = 0
        for i in res:
            if i in ('pl'):
                continue
            itemcount += 1
            # section header == aa.wikipedia (x z y)
            finalpage += u'\n\n== %s.wikipedia (%i z %i) ==' % (i,redirlist[i]['marked'], redirlist[i]['count'])
            # items
            for a in sorted(redirlist[i]['result']):
                finalpage += u'\n# [[:%s:%s]]' % (i,a)

        finalpage += footer 

        success = True
        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        outpage.text = finalpage

        if self.getOption('test'):
            pywikibot.output(outpage.title())
        
        outpage.save(summary=self.getOption('summary'))
        #if not outpage.save(finalpage, outpage, self.summary):
        #   pywikibot.output(u'Page %s not saved.' % outpage.title(asLink=True))
        #   success = False
        return(success)

    def interwikiGenerator(self,wdpage,namespace=0):
        # yield a list of categories based on wikidata sitelinks
        for i in wdpage['sitelinks']:
            if i.endswith('wiki'):
                lang = self.wikiLangTranslate(i[:-4])
                try:
                    if namespace == 14:
                        yield pywikibot.Category(pywikibot.Site(lang,'wikipedia'), wdpage['sitelinks'][i])
                    else:
                        yield pywikibot.Page(pywikibot.Site(lang,'wikipedia'), wdpage['sitelinks'][i])
                except:
                    pywikibot.output('ERROR: site %s does not exist!' % lang)

    def checkInterwiki(self,page,lang):
        """Check if lang is in list of interwikis"""
        if self.getOption('test3'):
            pywikibot.output(u'[%s] Treating (checkInterwiki): %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),page.title()))
        try:
            wd = pywikibot.ItemPage.fromPage(page)
            wdcontent = wd.get()
            return (lang in wdcontent['sitelinks'].keys())
        except pywikibot.NoPage:
            return(False)

    def wikiLangTranslate(self,lang):
        #change lang in case of common errors, renames etc.
        translateTable = {
            'dk': 'da',  # Wikipedia, Wikibooks and Wiktionary only.
            'jp': 'ja',
            'nb': 'no',  # T86924
            'minnan': 'zh-min-nan',
            'nan': 'zh-min-nan',
            'zh-tw': 'zh',
            'zh-cn': 'zh',
            'nl_nds': 'nl-nds',
            'be-x-old': 'be-tarask',
            'be_x_old': 'be-tarask',
        }

        if lang in translateTable.keys():
            pywikibot.output('Translated [%s] -> [%s]' % (lang,translateTable[lang]))
            return (translateTable[lang])
        else:
            pywikibot.output('unTranslated [%s]' % lang)
            return(lang)


    def treat(self,page):
        result = {}
        txt = page.text
        if self.getOption('test3'):
            pywikibot.output(u'PAGE:%s' % txt)

        #
        try:
            wd = pywikibot.ItemPage.fromPage(page)
            wdcontent = wd.get()
            if self.getOption('test'):
                pywikibot.output(wdcontent['sitelinks'].keys())
        except:
            pywikibot.output('WikiData page for %s do not exists' % page.title(asLink=True))
            return(None)

        for c in self.interwikiGenerator(wdcontent,namespace=14):
            if self.getOption('test'):
                pywikibot.output(c.title())
            code = c.site.code
            if self.getOption('test2'):
                pywikibot.output('Code:%s' % c.site.code)
                #if lang not in ('be-tarask','tt'):
                if code not in ('en'):
                    continue
            if self.getOption('test'):
                pywikibot.output(u'P:%s' % c.title(asLink=True,forceInterwiki=True))
                pywikibot.output(u'SI:%s' % c.site.siteinfo)

            result[code] = self.getArticles(c)
        if self.getOption('test4'):
            pywikibot.output(result)
        return(result)

    def getArticles(self,cat):
        #return a list of article titles without pl.interwiki
        if self.getOption('test5'):
            pywikibot.output("get articles")
        count = 0
        marked = 0
        result = []
        lang = cat.site.code
        for a in cat.articles():
            if self.getOption('test'):
                pywikibot.output(u'[%s] %s.wiki: [%i of %i] %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),lang,marked,count,a.title(asLink=True,forceInterwiki=True)))
            count += 1
            """
            if a.namespace() == 1:
                a = a.toggleTalkPage()
            if not self.checkInterwiki(a,'plwiki'):
                result.append(a.title())
                marked += 1
                if self.getOption('test3'):
                    pywikibot.output(u'[%s] appended: %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),a.title(asLink=True,forceInterwiki=True)))
            """
        return({'count':count,'marked':marked,'result':result})

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
