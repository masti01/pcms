#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An incomplete sample script by masti for creating statistics/listings pages

This is not a complete bot; rather, it is a template from which simple
bots can be made. You can rename it to mybot.py, then edit it in
whatever way you want.

Use global -simulate option for test purposes. No changes to live wiki
will be done.

Call:
	python pwb.py masti/ms-contains.py -catr:"Posłowie do Knesetu" -outpage:"Wikipedysta:Andrzei111/Izrael/bez Kneset" \
		-summary:"Bot uaktualnia tabelę" -text:"{{Kneset" -negative

	python pwb.py masti/ms-contains.py -weblink:'isap.sejm.gov.pl' -outpage:"Wikipedysta:mastiBot/isap" \
		-summary:"Bot uaktualnia tabelę" -text:"http://isap\.sejm\.gov\.pl/Download\?id=WD[^\s\]\|]*" -ns:0 -regex

	python pwb.py masti/ms-contains.py -weblink:'isap.sejm.gov.pl' -outpage:"Wikipedysta:mastiBot/isap" \
		-summary:"Bot uaktualnia tabelę" -text:"(?P<result>http://isap\.sejm\.gov\.pl/Download\?id=WD[^\s\]\|]*)" -ns:0 -regex

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

-regex:           treat text as regex - should contain <result> group. if not whole match will be used

-title:           search in title not page.text

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

from pywikibot.bot import (
    SingleSiteBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)
from pywikibot.tools import issue_deprecation_warning
import re
import urllib2
import datetime

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
            'text': 'Test',  #default search string 'Test' is default
            'top': False,  # append text on top of the page
            'outpage': u'Wikipedysta:mastiBot/test', #default output page
            'maxlines': 1000, #default number of entries per page
            'negative': False, #if True mark pages that DO NOT contain search string
            'test': False, #switch on test functionality
            'regex': False, #use text as regex
            'title': False, #search in page.title not in page.text
        })

        # call constructor of the super class
        super(BasicBot, self).__init__(site=True, **kwargs)
        #super(SingleSiteBot, self).__init__(site=True, **kwargs)

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

	header = u"Ta strona jest okresowo uaktualniana przez [[Wikipedysta:MastiBot|MastiBota]]. Ostatnia aktualizacja ~~~~~. \n"
	header += u"Wszelkie uwagi proszę zgłaszać w [[Dyskusja_Wikipedysty:Masti|dyskusji operatora]].\n\n"
        
        reflinks = [] #initiate list
        licznik = 0
        marked = 0
        for page in self.generator:
	    licznik += 1
            pywikibot.output(u'Treating #%i (marked:%i): %s' % (licznik, marked, page.title()))
            refs = self.treat(page) # get (name)
            if refs:
                if not refs in reflinks:
                    #test
                    pywikibot.output(refs)
                    reflinks.append(refs)
                    marked += 1
                else:
                    #test
                    pywikibot.output(u'Already marked')

        footer = u'\n'
        footer += u'\n\nPrzetworzono ' + str(licznik) + u' stron'

        outputpage = self.getOption('outpage')

        result = self.generateresultspage(reflinks,outputpage,header,footer)
        

    def generateresultspage(self, redirlist, pagename, header, footer):
        """
        Generates results page from redirlist
        Starting with header, ending with footer
        Output page is pagename
        """
        maxlines = int(self.getOption('maxlines'))
        finalpage = header
        #res = sorted(redirlist, key=redirlist.__getitem__, reverse=False)
        res = sorted(redirlist)
        itemcount = 0
        for i in res:

            if self.getOption('regex'):
                title, link = i
            else:
                title = i
            finalpage += u'\n# [[' + title + u']]'
            if self.getOption('regex'):
                finalpage += u' - ' + link
            itemcount += 1
            if itemcount > maxlines-1:
                pywikibot.output(u'*** Breaking output loop ***')
                break

        # if no results found to be reported
        if not itemcount:
            finalpage += u"\n\n'''Brak wyników'''\n\n"

        finalpage += footer 

        #pywikibot.output(finalpage)
        success = True
        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        outpage.text = finalpage

        pywikibot.output(outpage.title())
        
        outpage.save(summary=self.getOption('summary'))
        #if not outpage.save(finalpage, outpage, self.summary):
        #   pywikibot.output(u'Page %s not saved.' % outpage.title(asLink=True))
        #   success = False
        return(success)
 
    def treat(self, page):
        """
        Returns page title if param 'text' in page
        """

        if self.getOption('title'):
            source = page.title()
        else:
            source = page.text

        # new version
        if self.getOption('regex'):
            if u'?P<result>' in self.getOption('text'):
                resultR =  self.getOption('text')
            else:
                resultR = u'(?P<result>' + self.getOption('text') + u')'
            if self.getOption('test'):
                pywikibot.output(resultR)
            match = re.search(resultR, source)
            if (match and self.getOption('negative')) or (not match and not self.getOption('negative')) :
                return(None)
            return(page.title(),match.group('result'))
        else:  
            isIn = self.getOption('text') in source
            if not isIn and self.getOption('negative'):
                if self.getOption('test'):
                    pywikibot.output('NEGATIVE:Text not found')
                return(page.title())
            if isIn and not self.getOption('negative'):
                if self.getOption('test'):
                    pywikibot.output('POSITIVE:Text found')
                return(page.title())
            return(None)

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
