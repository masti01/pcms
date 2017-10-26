#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A script by masti for printing a list of interwiki pages

Call:
python pwb.py masti/ms-listinterwiki.py -page:"Kategoria:Artykuły na medal" -outpage:"Wikipedysta:mastiBot/support/AnM" -summary:"Bot aktualizuje listę"
python pwb.py masti/ms-listinterwiki.py -page:"Kategoria:Dobre artykuły" -outpage:"Wikipedysta:mastiBot/support/DA" -summary:"Bot aktualizuje listę"
python pwb.py masti/ms-listinterwiki.py -page:"Kategoria:Listy na medal" -outpage:"Wikipedysta:mastiBot/support/LnM" -summary:"Bot aktualizuje listę"


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
from datetime import datetime
import sys
import os

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
            'outfile': 'masti/testfile', #default results file
            'maxlines': 1000, #default number of entries per page
            'test': False,
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

        pages = []

        #header = u'{{Wikipedia:Brakujące artykuły/Nagłówek}}\n\n'
        header = u'Kategorie zawierające '
        if self.getOption('good'):
            header += 'Dobre Artykuły'
        elif self.getOption('lists'):
            header += 'Listy na Medal'
        else:
            header += 'Artykuły na Medal'

        header += ' w innych Wikipediach.\n\n'
        header += 'Ta strona jest okresowo uaktualniana przez [[Wikipedysta:MastiBot|bota]].\n\n'
        header += "Ostatnia aktualizacja: '''" + datetime.now().strftime("%Y-%m-%d %H:%M:%S (CEST)") +".\n\n"
        header += 'Wszelkie uwagi proszę zgłaszać w [[Dyskusja_Wikipedysty:Masti|dyskusji operatora]].\n\n'

        footer = u''

        for page in self.generator:
            pages = self.genInterwiki(page)

        self.generateresultspage(pages, self.getOption('outpage'), header, footer)
        return

    def lang(self,template):
        return(re.sub(ur'\[\[(.*?):.*?\]\]',ur'\1',template))

    def genInterwiki(self,page):
            # gen interwiki sites list
            iw = {}
            wkpd = page.site.family
            d = page.data_item()
            if self.getOption('test'):
                pywikibot.output(u'WD: %s' % d.title() )
            dataItem = d.get()
            sitelinks = dataItem['sitelinks']
            #print sitelinks
            for s in sitelinks.keys():
                if self.getOption('test'):
                    pywikibot.output(u'SL iw: %s' % d)
                try:
                    family = re.sub(ur'.*(wiki|voyage|quote|books|news|source|versity|wikt)', ur'\1',s)
                except:
                    if self.getOption('test'):
                        pywikibot.output('wrong family')
                    continue
                try:
                    site = re.sub(ur'(.*)(wiki|voyage|quote|books|news|source|versity|wikt)', ur'\1',s)
                    if site == u'be_x_old':
                        site = u'be-tarask'
                    site = re.sub(ur'_',ur'-',site)
                except:
                    if self.getOption('test'):
                        pywikibot.output('wrong site')
                    continue
                #print site, family
                if family != 'wiki' or not site in wkpd.codes :
                    if self.getOption('test'):
                        pywikibot.output('error:%s',family)
                    continue
                ssite = pywikibot.Site(site,fam='wikipedia')
                spage = pywikibot.Category( ssite, title=sitelinks[s] )
                pywikibot.output(u"%s;%s" % (site,spage.title()) )
                iw[site] =  spage.title()

            print iw
            return(iw)

    def generateresultspage(self, redirlist, pagename, header, footer):
        """
        Generates results page from redirlist
        Starting with header, ending with footer
        Output page is pagename
        """
        finalpage = header
        #res = sorted(redirlist, key=redirlist.__getitem__, reverse=False)
        res = sorted(redirlist.keys())
        itemcount = 0
        for i in res:
            if i in ('pl'):
                continue
            itemcount += 1
            finalpage += u'# [[:' + i + u':' + redirlist[i] +u']]\n'
            if itemcount > int(self.getOption('maxlines'))-1:
                pywikibot.output(u'*** Breaking output loop ***')
                break

        finalpage += footer 

        if self.getOption('test'):
            pywikibot.output(finalpage)
        success = True
        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        outpage.text = finalpage

        pywikibot.output(outpage.title())
        
        outpage.save(summary=self.getOption('summary'))
        #if not outpage.save(finalpage, outpage, self.summary):
        #   pywikibot.output(u'Page %s not saved.' % outpage.title(asLink=True))
        #   success = False
        return(success)


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
        if option in ('summary', 'text', 'outpage', 'outfile', 'maxlines'):
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
