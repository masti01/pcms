#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Call:
python pwb.py masti/ms-titles.py -page:A -maxlines:2000000 -outpage:"Wikipedysta:mastiBot/nazwiska z inicjałem"

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
import re
import codecs
from datetime import datetime

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
            'outpage': u'User:mastiBot/test', #default output page
            'maxlines': 1000, #default number of entries per page
            'test': False, # print testoutput
            'negative': False, #if True negate behavior i.e. mark pages that DO NOT contain search string
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
        """TEST"""
        pywikibot.output(u'THIS IS A RUN METHOD')
        outputpage = self.getOption('outpage')
        pywikibot.output(u'OUTPUTPAGE:%s' % outputpage)

	header = u"Ta strona jest okresowo uaktualniana przez [[Wikipedysta:MastiBot|MastiBota]]. Ostatnia aktualizacja ~~~~~. \n"
	header += u"Wszelkie uwagi proszę zgłaszać w [[Dyskusja_Wikipedysty:Masti|dyskusji operatora]].\n\n"
        header +=u'\n{| class="wikitable sortable" style="font-size:85%;"'
        header +=u'\n|-'
        header +=u'\n!Nr'
        header +=u'\n!krótka nazwa'
        header +=u'\n!lista artykułów'


        resTitles = {}

        filepath = 'masti/titles'
        with codecs.open(filepath, 'r') as fp:
            fp.readline()
            titles = fp.read().splitlines()

        pywikibot.output('Lines: %i' % len(titles))

        #pywikibot.output(titles[:10])

        count = 0
        for t in titles:
            count += 1
            try:
                result = self.treat_page(t)
            except:
                continue
            if result:
                pywikibot.output('%i:%s' % (count,result))
                self.addTitle(resTitles,t,result)
            if count >= int(self.getOption('maxlines')):
                break

        pywikibot.output(resTitles)
        #for p in self.generator:
        #    pywikibot.output(u'Treating: %s' % p.title())

        footer = u'\n|}'
        footer += u'\n\nPrzetworzono ' + str(count) + u' stron'

        self.generateresultspage(resTitles,self.getOption('outpage'),header,footer)


    def addTitle(self,titles,longt,shortt):
        if shortt in titles.keys():
            titles[shortt].append(longt)
        else:
            titles[shortt] = [longt]

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
        if self.getOption('test'):
            pywikibot.output(u'GENERATING RESULTS')
        for i in res:

            if self.getOption('test'):
                pywikibot.output(i)

            itemcount += 1

            finalpage += re.sub(ur'_',' ', u'\n|-\n| %i || [[%s]] || [[%s]]' % (itemcount,i,']],<br />[['.join(redirlist[i])))


        finalpage += footer 
        
        if self.getOption('test'):
            pywikibot.output(finalpage)
        success = True
        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        outpage.text = finalpage

        if self.getOption('test'):
            pywikibot.output('OUTPAGE:%s' % outpage.title())
            pywikibot.output('PAGESIZE: %i' % len(finalpage))
            pywikibot.output('START SAVING: %s' % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        outpage.save(summary=self.getOption('summary'))
        #if not outpage.save(finalpage, outpage, self.summary):
        #   pywikibot.output(u'Page %s not saved.' % outpage.title(asLink=True))
        #   success = False
        return(success)
        

    def treat_page(self,title):
        """Load the given page, do some changes, and save it."""
        midinitR = re.compile(ur'(?m)^(?P<first>[^\d_ \.]*)_([A-Z]\.)+_(?P<last>[^\d_ \(\n\.]*)($|_\()',re.UNICODE)
        #midinitR = re.compile(ur'(?m)^(?P<first>[\w\-]+)_([A-Z]\.)+_(?P<last>[\w\-]+)($|_\()',re.UNICODE)
        #pywikibot.output(title)
        match = midinitR.match(title)
        if match:
            if match.group('first'):
                f = match.group('first')
            if match.group('last'):
                l = match.group('last')
            if f and l:
                short = f+'_'+l
                pywikibot.output(u'Match: %s->%s' % (title,short))
                return(short)
        return(None)



def templateWithNamedParams(self):
        """
        Iterate template as returned by templatesWithNames()

        @return: a generator that yields a tuple for each param of a template
            type: named, int
            name: name of param
            value: value of param
        @rtype: generator
        """
        # TODO

def templateArg(self, param):
        """
        return name,value for each template param

        input text in form "name = value"
        @return: a tuple for each param of a template
            named: named (True) or int
            name: name of param or None if numbered
            value: value of param
        @rtype: tuple
        """
        # TODO
        paramR = re.compile(ur'(?P<name>.*)=(?P<value>.*)')
        if '=' in param:
            match = paramR.search(param)
            named = True
            name = match.group("name").strip()
            value = match.group("value").strip()
        else:
           named = False
           name = None
           value = param
        #test
        pywikibot.output(u'name:%s:value:%s' % (name, value))
        return named, name, value

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
