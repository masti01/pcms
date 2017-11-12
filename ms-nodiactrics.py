#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Article to find miisng/potential doubled articles with or without dicatrical chararcters in title

Call:
    python pwb.py masti/ms-nodiactrics.py -catr:"Sportowcy" -summary:"Bot uaktualnia tabelę" -outpage:"Wikipedysta:MastiBot/Przekierowania bez diaktryków" -skippl
    python pwb.py masti/ms-nodiactrics.py -catr:"Sportowcy" -summary:"Bot uaktualnia tabelę" -outpage:"Wikipedysta:MastiBot/Przekierowania bez diaktryków/duble" -skippl -doubles

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

import sys 
reload(sys) 
sys.setdefaultencoding("utf-8")
import unicodedata
import re
import string

import pywikibot
from pywikibot import pagegenerators

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
            'outpage': u'User:mastiBot/test', #default output page
            'maxlines': 1000, #default number of entries per page
            'testprint': False, # print testoutput
            'negative': False, #if True negate behavior i.e. mark pages that DO NOT contain search string
            'skippl': False, #try to assume if the title is polish based on chars used
            'doubles': False, #find when articles with and without diactrics exist
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

    def run(self):

        results = {}
        processed = {}

        #prepare new page with table
	header = u"Ta strona jest okresowo uaktualniana przez [[Wikipedysta:MastiBot|bota]]. Ostatnia aktualizacja ~~~~~. \nWszelkie uwagi proszę zgłaszać w [[Dyskusja_Wikipedysty:Masti|dyskusji operatora]]."
	header += u"\n<small>"
	header += u"\n*Legenda:"
	header += u"\n*:'''Hasło''' - Tytuł hasła"
	header += u"\n*:'''Przekierowanie''' - Brakujące przekierowanie"
	header += u"\n</small>\n"
	header += u'{| class="wikitable" style="font-size:85%;"\n|-\n!Lp.\n!Hasło\n!Przekierowanie'

        footer = u'\n|}'

        counter = 1
        marked = 0
        skipped = 0
        for page in self.generator:
            if self.getOption('test'):
                pywikibot.output(u'Processing #%i (%i marked, %i skipped):%s' % (counter, marked, skipped, page.title(asLink=True)))
            counter += 1
            if page.title() in processed.keys():
                if self.getOption('test'):
                    pywikibot.output(u'Already done...')
                skipped += 1
                processed[page.title()] += 1
                continue
            processed[page.title()] = 1
            res = self.treat(page)
            if res:
                marked += 1
                results[page.title()] = res

        self.generateresultspage(results, self.getOption('outpage'), header, footer)
        if self.getOption('test'):
            pywikibot.output(processed)
            pywikibot.output(u'Processed #%i (%i marked, %i skipped)' % (counter, marked, skipped))
        

    def treat(self, page):
        """
        Check if page with .title() without diactrics exist
        If no: return title without diactrics
        If yes: return None
        """
        title = self.noDisambig(page.title())
        
        if self.getOption('skippl'):
           if self.assumedPolish(title):
               if self.getOption('test'):
                   pywikibot.output(u'Assumed polish name:%s' % title)
               return(None)

        noDiactricsTitle = self.strip_accents(title)
        if self.getOption('test'):
              pywikibot.output(u'Diactrics stripped:%s' % noDiactricsTitle)
        if noDiactricsTitle == title:
            if self.getOption('test'):
                pywikibot.output(u'No diactrics found:%s' % title)
            return(None)

        noDPage = pywikibot.Page(pywikibot.Site(), noDiactricsTitle)
        if not self.getOption('doubles') and not noDPage.exists():
            return(noDiactricsTitle)
        elif self.getOption('doubles') and noDPage.exists() and not noDPage.isRedirectPage():
            return(noDiactricsTitle)
        else:
            if self.getOption('test'):
                pywikibot.output(u'Diactrics page exists:%s' % noDiactricsTitle)
            return(None)

    def noDisambig(self, text):
        if self.getOption('test'):
            pywikibot.output(u'%s-->%s' % (text, re.sub(ur' \(.*?\)', u'', text)) )
        return(re.sub(ur' \(.*?\)', u'', text))

    def strip_accents(self,text):
        """
        Strip accents from input String.

        :param text: The input string.
        :type text: String.

        :returns: The processed String.
        :rtype: String.
        """
        #try:
        #    text = unicode(text, 'utf-8')
        #except NameError: # unicode is a default on python 3 
        #    pass
        
        #text = unicodedata.normalize('NFD', text)
        #text = text.encode('ascii', 'ignore')
        #text = text.decode("utf-8")
        trans = [
            ('Đ', 'D'),
            ('đ', 'd'),
            ('ð', 'd'),
            ('Ł', 'L'),
            ('ł', 'l'),
            ('ß', 'ss'),
            ('ñ', 'n'),
            ('Ä', 'Ae'),
            ('ä', 'ae'),
            ('Ö', 'Oe'),
            ('ö', 'oe'),
            ('Ü', 'Ue'),
            ('ü', 'ue'),
            ('Å', 'Aa'),
            ('å', 'aa'),
            ('Ø', 'Oe'),
            ('ø', 'oe'),
            ('Æ', 'Ae'),
            ('æ', 'ae'),
            ('Œ', 'Oe'),
            ('œ', 'oe'),
        ]

        text = self.multisub(trans, text)
        if self.getOption('test'):
            pywikibot.output(text)
            pywikibot.input('Waiting...')
        return str(''.join((c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')))

    def assumedPolish(self,text):
        """
        Try to verify if the text is in Polish
        """
        polishChars = [u'ą',u'ć',u'ę',u'ń',u'ó',u'ś',u'ź',u'ż',u'Ą',u'Ć',u'Ę',u'Ń',u'Ó',u'Ś',u'Ź',u'Ż']
        for c in polishChars:
            if c in text:
                return(True)
        return(False)

    def generateresultspage(self, rlist, pagename, header, footer):
        """
        Generates results page from rlist
        Starting with header, ending with footer
        Output page is pagename
        """
        finalpage = header
        #res = sorted(redirlist, key=redirlist.__getitem__, reverse=True)
        res = rlist
        linkcount = 1
        for i in res:
            finalpage += u'\n|-\n| ' + str(linkcount) + u' || [[' + i + u']] || [[' + rlist[i] + u']]'
            linkcount += 1
        finalpage += footer

        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        outpage.text = finalpage
        outpage.save(summary=self.getOption('summary'))

        if self.getOption('test'):
            pywikibot.output(rlist)
        return(res)

    def multisub(self, subs, subject):
        "Simultaneously perform all substitutions on the subject string."
        pattern = '|'.join('(%s)' % re.escape(p) for p, s in subs)
        substs = [s for p, s in subs]
        replace = lambda m: substs[m.lastindex - 1]
        return re.sub(pattern, replace, subject)

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
