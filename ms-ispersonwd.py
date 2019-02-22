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
from pywikibot.page import Claim, Property
from pywikibot.site import DataSite
from pywikibot import date

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

class Person(object):

    def __init__(self):
        self.title = None
        self.dob = None #Date of birth
        self.dod = None #Date of death
        self.occupation = [] #list of occupations
        self.instanceof = None
        self.description = None
        self.sex = None
        self.dobprecision = 11 #date precision for birth
        self.dodprecision = 11 #date precision for death

    def personPrint(self):
        pywikibot.output('Title:%s' % self.title)
        pywikibot.output('Is instance of:%s' % self.instanceof)
        pywikibot.output('Date of birth:%s' % self.dob)
        pywikibot.output('Date of birth precision:%s' % self.precision(self.dobprecision))
        pywikibot.output('Date of death:%s' % self.dod)
        pywikibot.output('Date of death precision:%s' % self.precision(self.dodprecision))
        pywikibot.output('Sex:%s' % self.sex)
        pywikibot.output('Occupation:%s' % ",".join(self.occupation))

    def centuryDecade(self,date): 
        #return decade of century i.e. 'lata 20. 20 wieku'
        if date > 0:
            return(pywikibot.date.formats['DecadeAD']['pl'](date))
        else:
            return(pywikibot.date.formats['DecadeBC']['pl'](date))

    def centuryFromDate(self,date):
        #return century from give wbTime
        year = date.year
        if year % 100:
            return(int(1+year/100))
        else:
            return(int(year/100))

    def millenniumFromDate(self,date):
        #return century from give wbTime
        year = date.year
        if year % 1000:
            return(int(1+year/1000))
        else:
            return(int(year/1000))

    def millennium(self,date):
        #return millennium i.e. '20 wieku'
        mill = self.millenniumFromDate(date)
        if mill > 0:
            return('%i tysiąclecie' % mill)
        else:
            return('%i tysiąclecie p.n.e.' % -1*mill)

    def century(self,date):
        #return century i.e. '20 wieku'
        if date > 0:
            return(pywikibot.date.formats['CenturyAD']['pl'](self.centuryFromDate(date)))
        else:
            return(pywikibot.date.formats['CenturyBC']['pl'](self.centuryFromDate(date)))

    def formatDate(self,date,maxPrecision=None):
        #return date formatted according to date.precision
        #pywikibot.output('Format Date:%i' % date.precision)
        if maxPrecision:
            prec = min(maxPrecision,date.precision)
        else:
            prec = date.precision
        if prec == 11: #days
            return('%d-%02d-%02d' % (date.year,date.month,date.day))
        elif prec == 10: #months
            return('%d-%02d' % (date.year,date.month))
        elif prec == 9: #years
            return('%d' % date.year)
        elif prec == 8: #10 years
            return(self.centuryDecade(date))
        elif prec == 7: #100 years
            return(self.century(date))
        elif prec == 6: #1000 years
            return(self.millennium(date))
        return(date)

    def setDoB(self,date):
        try:
            self.dob = self.formatDate(date,maxPrecision=9)
        except:
            self.dob = ''
        self.dobprecision = date.precision

    def setDoD(self,date):
        try:
            self.dod = self.formatDate(date,maxPrecision=9)
        except:
            self.dod = ''
        self.dodprecision = date.precision


    def precision(self,prec):
        #return precision text from numeric value prec
        datePrecision = {
		0:'1 Gigayear',
		1:'100 Megayears',
		2:'10 Megayears',
		3:'Megayear',
		4:'100 Kiloyears',
		5:'10 Kiloyears',
		6:'Kiloyear',
		7:'100 years',
		8:'10 years',
		9:'years',
		10:'months',
		11:'days',
		12:'hours (unused)',
		13:'minutes (unused)',
		14:'seconds (unused)',
        }
        return(datePrecision[prec])



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
        #pywikibot.output(u'OUTPUTPAGE:%s' % outputpage)
        maxlines = self.getOption('maxlines')
        #pywikibot.output(u'MAXLINES:%s' % maxlines)
        pywikibot.output('Available formats:%s' % pywikibot.date.formats.keys())
        count = 0
        for p in self.generator:
            count += 1
            pywikibot.output(u'#%i:[%s] Treating: %s' % (count,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),p.title()))
            #pywikibot.output('INTERWIKI:%i' % self.treat(p))
            if self.treat(p):
                pywikibot.output('PERSON FOUND:[[%s]]' % p.title())
            else:
                pywikibot.output('PERSON NOT FOUND:[[%s]]' % p.title())

    # wersja bez strony pomocniczej via interwikidata

    def interwikiGenerator(self,wdpage):
        for i in wdpage['sitelinks']:
            if i.endswith('wiki'):
                lang = i[:-4]
                print lang
                yield pywikibot.Category(pywikibot.Site(lang,'wikipedia'), wdpage['sitelinks'][i])

    def getLabel(self,ent,lang):
        result = None
        entcontent = ent.get()
        for l in lang:
            try:
                #pywikibot.output('get label for:%s' % l)
                return(entcontent['labels'][l])
            except:
                continue
        return(result)

    def treat(self, page):

        sex = { 'Q6581097':'mężczyzna', 'Q6581072':'kobieta', 'Q1097630':'obojnak'}
        results = {} # {lang,catname,{count,listofarticles}}
        lineR = re.compile(ur'(?m)^# \[\[:(?P<lang>.*?):(?P<cat>.*?):(?P<catname>.*?)\]\]')

        obj = Person()

        try:
            wd = pywikibot.ItemPage.fromPage(page)
            wdcontent = wd.get()
            pywikibot.output(wdcontent['claims'].keys())
            #pywikibot.output(wdcontent['sitelinks'].keys())
            #return ('plwiki' in wdcontent['sitelinks'].keys())
        except:
            pywikibot.output('WikiData page do not exists')
            return(None)

        wbs = pywikibot.Site('wikidata','wikidata')

        #if 'P21' in wdcontent['claims'].keys():
        #    pywikibot.output('Płeć:%s' % wdcontent['claims']['P21'])

        for pid, claims in wdcontent['claims'].items():
            for claim in claims:
                trg = claim.getTarget()
                prp = pywikibot.PropertyPage(wbs,title=pid)
                #prp = pywikibot.PropertyPage(wbs,title=pid,ns='Property')
                #pywikibot.output('Property type:%s' % prp)
                #pywikibot.output('Property type:%s' % prp.type())

                prpcontent = prp.get()
                #pywikibot.output('Property content:%s' % self.getLabel(prp,['xhs','pl','sco','en']))
                #pywikibot.output('Property:%s Value:%s' % (pid,trg))
                obj.title = page.title()
                if pid == 'P31':
                     pywikibot.output('Jest to:%s' % trg.title())
                     if trg.title() == 'Q5':
                         pywikibot.output('CZŁOWIEK!')
                         return(True)
                     else:
                         pywikibot.output('coś innego :(')


                '''
                if pid in ['P21','P569','P570','P106']:
                    pywikibot.output('P:%s, V:%s' % (self.getLabel(prp,['pl','en']),trg))
                if pid == 'P21':
                     pywikibot.output('płeć:%s' % sex[trg.title()])
                     obj.sex = sex[trg.title()]
                if pid == 'P569':
                    pywikibot.output('FormatDate:%s' % date.monthName('pl', trg.month))
                    obj.setDoB(trg)
                if pid == 'P570':
                    obj.setDoD(trg)
                    obj.dodprecision = trg.precision
                if pid == 'P106':
                    obj.occupation.append(self.getLabel(trg,['pl','en']))
                
                if pid == 'P625':
                    pywikibot.output('Coords:%s' % trg) 
                '''

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
