#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Bot to list potential disambigs and disambig errors
Call;
python pwb.py masti/ms-disambigs.py -start:'!' -outpage:'Wikipedysta:mastiBot/Ujednoznacznienia' -progress -summary:'Bot aktulizuje tabelę ujednoznacznień' -pt:0


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
import datetime
import pickle
from pywikibot import (
    config, config2,
)

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
            'progress': False, # report progress
            'load': False, # load data from file
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

        result = {}
        pagecount = 0

        if self.getOption('load'):
            try:
                with open('masti/disambigs.dat', 'rb') as datfile:
                    result = pickle.load(datfile)
            except (IOError, EOFError):
                # no saved history exists yet, or history dump broken
                result = {}

        for p in self.generator:
            pagecount += 1
            if self.getOption('test') or self.getOption('progress'):
                pywikibot.output(u'[%s] Treating:[%s] %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),pagecount,p.title()))
            basic = self.basicTitle(p.title())

            if basic in result.keys():
                result[basic]['articles'].append(p.title())
                if p.isDisambig():
                    result[basic]['disambig'] = p.title()
            else:
                if p.isDisambig():
                    result[basic] = {'articles':[p.title()], 'disambig':p.title(), 'redir':None}
                else:
                    result[basic] = {'articles':[p.title()], 'disambig':None, 'redir':None}
        if self.getOption('test'):
            pywikibot.output(result)

        result = self.cleanupList(result)
        result = self.checkExistence(result)
        result = self.solveRedirs(result)
        result = self.solveDisambTargets(result)
        result = self.guessDisambig(result)

        self.save(result)

        self.generateresultspage(result, self.getOption('outpage'), self.header(), self.footer())

    def save(self,results):
        """Save the .dat file to disk."""
        #test output
        pywikibot.output('PICKLING at %s' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        with open('masti/disambigs.dat', 'wb') as f:
            pickle.dump(results, f, protocol=config.pickle_protocol)

    def cleanupList(self,reslist):
        #remove unnecessary records
        #where only 1 article and not disambig
        d = {}
        pagecount = 0
        for p in reslist.keys():
            pagecount += 1
            if self.getOption('test') or self.getOption('progress'):
                pywikibot.output(u'[%s] cleanupList:[%i] %s %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),pagecount,p,reslist[p]))
            if reslist[p]['disambig']:
                if  p == reslist[p]['disambig']:
                    if self.getOption('test'):
                        pywikibot.input(u'skipped')
                    continue
            else:
                if len(reslist[p]['articles']) == 1 and p == reslist[p]['articles'][0] :
                    if self.getOption('test'):
                        pywikibot.input(u'skipped')
                    continue
            if self.getOption('test'):
                pywikibot.input('P:%s D:%s' % (p,reslist[p]['disambig']))
            d[p] = reslist[p]
            if self.getOption('test'):
                pywikibot.input(u'solveRedirs: %s' % d[p])

        return(d)

    def solveRedirs(self,reslist):
        # check if arts are redirs and find targets
        pagecount = 0
        for p in reslist.keys():
            pagecount += 1
            if self.getOption('test') or self.getOption('progress'):
                pywikibot.output(u'[%s] solveRedirs:[%i] %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),pagecount,p))
            page = pywikibot.Page(pywikibot.Site(),p)
            if page.isRedirectPage():
                reslist[p]['redir'] = page.getRedirectTarget().title()
                if not reslist[p]['disambig']:
                    reslist[p]['disambig'] = page.getRedirectTarget().title()
        return(reslist)

    def solveDisambTargets(self,reslist):
        # if disambig defined find not listed targets
        pagecount = 0
        for p in reslist.keys():
            pagecount += 1
            if self.getOption('test') or self.getOption('progress'):
                pywikibot.output(u'[%s] getDisambTargets:[%i] %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),pagecount,p))
            if reslist[p]['disambig']:
                page = pywikibot.Page(pywikibot.Site(),reslist[p]['disambig'])
                reslist[p]['articles'] = self.getDisambTargets(page,reslist[p]['articles'])

        return(reslist)

    def getDisambTargets(self,page,reslist):
        # get a list of disamb targets and add to article list
        titleR =  re.compile(ur'(?m)^\* *\[\[(?P<title>[^\|\]]*)')
      
        for p in titleR.finditer(page.text):
            if p.group('title') not in reslist:
                reslist.append(p.group('title'))
        return(reslist)

    def checkExistence(self,reslist):
        # check if main topic exists
        
        pagecount = 0
        for p in reslist.keys():
            pagecount += 1
            if self.getOption('test') or self.getOption('progress'):
                pywikibot.output(u'[%s] checkExistence:[%i] %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),pagecount,p))
            page = pywikibot.Page(pywikibot.Site(),p)
            reslist[p]['exists'] = page.exists()

        return(reslist)

    def guessDisambig(self,reslist):
        # look for possible disambigs if None
        #
        pagecount = 0
        for p in reslist.keys():
            pagecount += 1
            if self.getOption('test') or self.getOption('progress'):
                pywikibot.output(u'[%s] guessDisambig:[%i] %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),pagecount,p))
            if not reslist[p]['exists']:
                reslist[p]['disambig'] = p
            elif not reslist[p]['disambig']:
                reslist[p]['disambig'] = p + ' (ujednoznacznienie)'

        return(reslist)

    def basicTitle(self,title):
        #return title without leading parenthesis section
        btR = re.compile(ur'(?m)(?P<basictitle>.*?) \(.*?\)(\/.*)?$')
        bt = btR.match(title)
        if bt:
            return(bt.group('basictitle'))
        else:
            return(title)

    def header(self):
	header = u"Ta strona jest okresowo uaktualniana przez [[Wikipedysta:MastiBot|MastiBota]]. Ostatnia aktualizacja '''~~~~~'''."
	header += u"\n\nWszelkie uwagi proszę zgłaszać w [[Dyskusja wikipedysty:Masti|dyskusji operatora]]."
	header += u"\n:<small>ZLista potencjalnie brakujących ujednoznacznień</small>"
        header +=u'\n\n{| class="wikitable sortable" style="font-size:85%;"'
        header +=u'\n|-'
        header +=u'\n!Nr'
        header +=u'\n!Artykuł'
        header +=u'\n!Cel'
        header +=u'\n!Ujednoznacznienie'
        header +=u'\n!Lista'
        return(header)

    def footer(self):
        footer = u'\n|}'
        return(footer)

    def generateresultspage(self, redirlist, pagename, header, footer):
        """
        Generates results page from redirlist
        Starting with header, ending with footer
        Output page is pagename
        """
        maxlines = int(self.getOption('maxlines'))
        finalpage = header
        #res = sorted(redirlist, key=redirlist.__getitem__, reverse=False)
        res = sorted(redirlist.keys())
        #res = redirlist
        itemcount = 1
        if self.getOption('test'):
            pywikibot.output(u'GENERATING RESULTS')
        for i in res:
            disamb = u'[[%s]]' % redirlist[i]['disambig'] if redirlist[i]['disambig'] else ''
            redir = u'[[%s]]' % redirlist[i]['redir'] if redirlist[i]['redir'] else ''

            if len(redirlist[i]['articles']) > 1:
                line = u'\n|-\n| %i || [[%s]] || %s || %s || [[%s]]' % ( itemcount, i, redir, disamb, ']]<br />[['.join(redirlist[i]['articles']) )
            else:
                if redirlist[i]['articles'][0] == i:
                    continue
                else:
                    line = u'\n|-\n| %i || [[%s]] || %s || %s || [[%s]]' % ( itemcount, i, redir, disamb, redirlist[i]['articles'][0] )
            itemcount += 1
            finalpage += line

        finalpage += footer 
        
        if self.getOption('test'):
            pywikibot.output(finalpage)
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
