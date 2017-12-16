#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An incomplete sample script by masti for creating statistics/listings pages

This is not a complete bot; rather, it is a template from which simple
bots can be made. You can rename it to mybot.py, then edit it in
whatever way you want.

Use global -simulate option for test purposes. No changes to live wiki
will be done.

This bot creates a pages with links to tennis players.

Call:
	python pwb.py masti/ms-psb.py -page:"Wikipedysta:PuchaczTrado/PSB" -maxlines:10000 -summary:"Bot uaktualnia tabelę"
	python pwb.py masti/ms-psb.py -page:"Wikipedysta:PuchaczTrado/PSB/Tabela" -maxlines:10000 -renew -summary:"Bot uaktualnia tabelę"

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

actionCounters = {
    'total':0,
    'blue':0,
    'red':0,
    'redirs':0,
    'disambigs':0
}

class Person(object):
    #Class to describe person from list
    def __init__(self):
        self.title = None
        self.dob = '' #Date of birth
        self.dod = '' #Date of death
        self.occupation = [] #list of occupations
        self.instanceof = None
        self.wditem = ''
        self.disambig = False
        self.description = ''
        self.sex = None
        self.wdexists = False
        self.link = None
        self.comment = None

    def personPrint(self):
        pywikibot.output('Link:%s' % self.link)
        pywikibot.output('Title:%s' % self.title)
        pywikibot.output('Wikidata exists:%s' % self.wdexists)
        pywikibot.output('Wikidata item:%s' % self.wditem)
        pywikibot.output('Is disambig:%s' % self.disambig)
        pywikibot.output('Is instance of:%s' % self.instanceof)
        pywikibot.output('Date of birth:%s' % self.dob)
        pywikibot.output('Date of death:%s' % self.dod)
        pywikibot.output('Sex:%s' % self.sex)
        try:
            pywikibot.output('Occupation:%s' % ",".join(self.occupation))
        except:
            pywikibot.output('Occupation: ERROR')
        pywikibot.output('Description:%s' % self.description)
        pywikibot.output('Comment:%s' % self.comment)

    def WDexists(self):
        return(self.wdexists)

    def isDisambig(self):
        return(self.disambig)

    def whatIs(self):
        if self.sex:
            return(self.sex)
        elif self.disambig:
            return('<strona ujednoznaczniająca>')
        elif self.instanceof:
            return(self.instanceof)
        else:
            return('<brak danych>')

    def DoB(self):
        return(self.dob)

    def DoD(self):
        return(self.dod)

    def Occupation(self):
        return(",".join(self.occupation))

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
            'outpage': u'Wikipedysta:mastiBot/test', #default output page
            'maxlines': 1000, #default number of entries per page
            'test': False, #test options
            'listscount': 1000, #max number of processed lists
            'labels': False, #show labels in WD Item
            'object': False, #show object content
            'testcount': 10000, #process only testcount items from input page
            'renew': False, #use original or generated pages as input
            'skip': 0, #skip that many first pages
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

    def getLabel(self,ent,lang):
        #get entity label in lang language with fallback
        entcontent = ent.get()
        for l in lang:
            try:
                #pywikibot.output('get label for:%s' % l)
                return(entcontent['labels'][l])
            except:
                continue
        return(None)

    def extractsection(self,page,section,level):
        # extract section of page returning it's content
        sectionR = re.compile(ur'(?s)={'+str(level)+'}\s*?'+section+'\s*?={'+str(level)+'}(?P<text>.*?)\n={'+str(level)+'} ')
        if self.getOption('test'):
            pywikibot.output(u'(?s)={'+str(level)+'}\s*?'+section+'\s*?={'+str(level)+'}(?P<text>.*?)\n={'+str(level)+'} ')
        return(sectionR.search(page.text).group('text'))

    def genpages(self,text,ns=0, rgx=ur'\[\[(?P<title>[^\|\]]*?)[\|\]]'):
        #generate pages based on wikilinks in text
        #titleR = re.compile(ur'\[\[(?P<title>[^\|\]]*?)[\|\]]')
        titleR = re.compile(rgx)

        for t in titleR.finditer(text):
            title = re.sub(ur'  ',' ',t.group('title'))
            page = pywikibot.Page(pywikibot.Site(),title)
            if page.namespace() == ns:
                yield page,t

    def header(self):
	header = u"Ta strona jest okresowo uaktualniana przez [[Wikipedysta:MastiBot|MastiBota]]. Ostatnia aktualizacja '''~~~~~'''."
	header += u"\n\nWszelkie uwagi proszę zgłaszać w [[Dyskusja wikipedysty:Masti|dyskusji operatora]]."
	header += u"\n:<small>Znalezione artykuły proszę wpisywać w kolumnie ''Link''</small>"
	header += u"\n:<small>Uwagi i komentarze kolumnie ''Uwagi''</small>"
        header +=u'\n\n{| class="wikitable sortable" style="font-size:85%;"'
        header +=u'\n|-'
        header +=u'\n!Nr'
        header +=u'\n!Link'
        header +=u'\n!Artykuł'
        header +=u'\n!Wikidane'
        header +=u'\n!Jest to'
        header +=u'\n!Data urodzenia'
        header +=u'\n!Data śmierci'
        header +=u'\n!Zajęcie'
        header +=u'\n!Opis'
        header +=u'\n!Uwagi'
        return(header)

    def footer(self):
        footer = u'\n|}'
        return(footer)

    def resetCounters(self):
        actionCounters['blue'] = 0
        actionCounters['red'] = 0
        actionCounters['redirs'] = 0
        actionCounters['disambigs'] = 0

    def run(self):

        reflinks = [] #initiate list
        gencount = 0
        for tpage in self.generator:
	    gencount += 1
            if self.getOption('test'):
                pywikibot.output(u'[%s]Treating #%i: %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), gencount, tpage.title()))

            #text = self.extractsection(tpage,'Artykuły zapoczątkowane przeze mnie',2)
            #if self.getOption('test'):
            #    pywikibot.output(u'[%s]L:%s T:%s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tpage.title(),text ))

            text = tpage.text

            count = 0
            for p,t in self.genpages(text,ns=2):
                count += 1
                if count <= int(self.getOption('skip')): 
                    continue
                if count > int(self.getOption('listscount')):
                    break
                if self.getOption('test'):
                    pywikibot.output(u'[%s][%i]L:%s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), count, p.title() ))
                refs = self.treat(p) 
                #if self.getOption('test'):
                #    pywikibot.output(refs)
                reflinks.append(refs)
                self.resetCounters()


        #footer += u'\n\nPrzetworzono ' + str(counter) + u' stron'

        outputpage = self.getOption('outpage')

        #result = self.generateresultspage(reflinks,outputpage,header,footer)

    def getData(self,page):
        #get data from page & WD
        #return Person object
        sex = { 'Q6581097':'mężczyzna', 'Q6581072':'kobieta'}

        obj = Person()
        obj.title = page.title()

        try:
            wd = pywikibot.ItemPage.fromPage(page)
            wdcontent = wd.get()
            obj.wditem = '[[:d:%s]]' % wd.title()
            obj.wdexists = True
            if self.getOption('labels'):
                pywikibot.output(wdcontent['claims'].keys())
        except:
            pywikibot.output('WikiData page do not exists')
            obj.wdexists = False
            return(obj)

        wbs = pywikibot.Site('wikidata','wikidata')

        for pid, claims in wdcontent['claims'].items():
            for claim in claims:
                trg = claim.getTarget()
                prp = pywikibot.PropertyPage(wbs,title=pid)

                prpcontent = prp.get()
                #pywikibot.output('Property content:%s' % self.getLabel(prp,['xhs','pl','sco','en']))
                #pywikibot.output('Property:%s Value:%s' % (pid,trg))
                if pid in ['P21','P569','P570','P106']:
                    if self.getOption('labels'):
                        pywikibot.output('P:%s, V:%s' % (self.getLabel(prp,['pl','en']),trg))
                if pid == 'P21':
                     obj.sex = sex[trg.title()]
                if pid == 'P31':
                     obj.instanceof = self.getLabel(trg,['pl','en'])
                if pid == 'P569':
                    try:
                        obj.dob = '{{L|%d}}' % trg.year
                    except:
                        obj.dob = ''
                if pid == 'P570':
                    try:
                        obj.dod = '{{L|%d}}' % trg.year
                    except:
                        obj.dod = ''
                if pid == 'P106':
                    lbl = self.getLabel(trg,['pl','en'])
                    if lbl:
                        obj.occupation.append(lbl)

        return(obj)

    def treat(self, page):
        #treat all links on page
        if self.getOption('renew'):
            linkR = ur'\|[ \d]*?\|\| *?\[\[(?P<title>[^\]]*)\]\]( *?\|\|.*?)*\|\| *(?P<description>.*)\|\|[ \t]*(?P<comment>.*)'
        else:
            linkR = ur'# \[\[(?P<title>[^|\]]*?)(\|.*?)?\]\]\s*?(?P<description>.*)'
        result = []

        text = page.text

        count = 0
        for p,t in self.genpages(text,rgx=linkR):
            count += 1
            if count > int(self.getOption('testcount')):
                break
            actionCounters['total'] += 1
            obj = Person()
            
            if self.getOption('test'):
                pywikibot.output(u'Treat:[%s][%i][%i]:%s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), actionCounters['total'], count, p.title() ))
            if not p.exists():
                actionCounters['red'] += 1
            else:
                actionCounters['blue'] += 1
            pp = p
            while pp.isRedirectPage():
                actionCounters['redirs'] += 1
                pp = pp.getRedirectTarget()
                if self.getOption('test'):
                    pywikibot.output(u'Redirect:[%s]:%s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pp.title() ))

            if pp.isDisambig():
                actionCounters['disambigs'] += 1
                obj = self.getData(pp)
                obj.instanceof = '<strona ujednoznaczniająca>'
                obj.disambig = True
                obj.title = pp.title()
                if self.getOption('test'):
                    pywikibot.output(u'Disambig:[%s][#%i]:%s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),actionCounters['disambigs'], pp.title() ))
            else:
                obj = self.getData(pp)


            obj.link = p.title()
            obj.description = t.group('description')
            if self.getOption('renew'):
                obj.comment = t.group('comment')

            if self.getOption('object'):
                obj.personPrint()
            result.append(obj)

        if self.getOption('renew'):
            self.generateresultspage(result,page.title(),self.header(),self.footer())
        else:
            self.generateresultspage(result,page.title()+'/Tabela',self.header(),self.footer())

    def generateresultspage(self, redirlist, pagename, header, footer):
        """
        Generates results page from redirlist
        Starting with header, ending with footer
        Output page is pagename
        """
        maxlines = int(self.getOption('maxlines'))
        finalpage = header
        #res = sorted(redirlist, key=redirlist.__getitem__, reverse=False)
        #res = sorted(redirlist)
        res = redirlist
        itemcount = 0
        if self.getOption('test'):
            pywikibot.output(u'GENERATING RESULTS')
        for i in res:

            if self.getOption('test'):
                #pywikibot.output(i)
                i.personPrint()
            itemcount += 1
            if i.WDexists():
                if i.isDisambig():
                    finalpage += u'\n|-\n| %i || [[%s]] || [[%s]] || %s || colspan=4 style="background-color:NavajoWhite; text-align:center;" | %s || %s || %s' % \
                      ( itemcount, i.link, i.title, i.wditem, i.whatIs(), i.description, i.comment )
                else:
                    finalpage += u'\n|-\n| %i || [[%s]] || [[%s]] || %s || %s || %s || %s || %s || %s || %s' % \
                      ( itemcount, i.link, i.title, i.wditem, i.whatIs(), i.DoB(), i.DoD(), i.Occupation(), i.description, i.comment )
            else:
                finalpage += u'\n|-\n| %i || [[%s]] || [[%s]] || %s || colspan=4 style="background-color:LightSteelBlue; text-align:center;" | <brak danych> || %s || %s' % \
                      ( itemcount, i.link, i.title, i.wditem, i.description, i.comment )

        finalpage += footer 

        finalpage += '\n\n=== Statystyka ==='
        finalpage += '\n* Istniejące: %i' % actionCounters['blue']
        finalpage += '\n* Nieistniejące: %i' % actionCounters['red']
        finalpage += '\n* Przekierowania: %i' % actionCounters['redirs']
        finalpage += '\n* Ujednoznacznienia: %i' % actionCounters['disambigs']
        
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
        if option in ('summary', 'text', 'outpage', 'maxlines', 'listscount', 'testcount', 'skip'):
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
