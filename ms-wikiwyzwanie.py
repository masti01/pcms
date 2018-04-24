#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Call:
python pwb.py masti/ms-wikiwyzwanie.py -page:"Wikipedia:Wikiwyzwanie/Hasła" -outpage:"Wikipedia:Wikiwyzwanie/Ranking" -pt:0 -summary:"Bot uaktualnia statystyki" 


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
from datetime import datetime
import pickle
from pywikibot import (
    config, config2,
)
import operator

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
    wikichallenge = {
        'articles':{},
        'users':{},
        'weeks':{},
        'days':{},
        'incdays':{},
        'positions':{},
    }

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
            'reset': False, # rebuild database from scratch
            'testpickle': False, # make verbose output for article list load/save
            'testdays': False, # make verbose output for days results
            'testinc': False, # make verbose output for incdays results
            'testweeks': False, # make verbose output for weekly results
            'testincdays': False, # make verbose output for incremental days results
            'testiw': False, # make verbose output for interwikis
            'testchange': False, # make verbose output for position changes

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

        header = '{{Wikipedia:Wikiwyzwanie/nawigacja}}\n\n'
        header += "Ostatnia aktualizacja przez bota: '''~~~~~'''.\n\n"
        header += "{{Spis treści}}\n\n"


        footer = '\n\n== Zobacz też ==\n'
        footer += '* [[%s/lista|Szczegółowa lista haseł i punktacji]]' % self.getOption('outpage')
      

        #load articleList from previous run
        self.loadArticleList()

        for p in self.generator:
            pywikibot.output(u'Treating: %s' % p.title())
            self.treat(p)

        # save list for the future
        self.pickleArticleList(self.wikichallenge)

        self.generateResultTable(self.wikichallenge,self.getOption('outpage'),header,footer)
        self.saveArticleList(self.wikichallenge,self.getOption('outpage')+'/lista',header,'')

    def treat(self,page):
        """Load the given page, do some changes, and save it."""
        text = page.text
        days = self.getDays(text)
        for d in days.keys():
            # d is day number
            artUsers = self.getArtsUsers(days[d]['body'])
            for t,u in artUsers:
                if t in self.wikichallenge['articles'].keys():
                    pywikibot.output('SKIPPING:[[%s]]' % t)
                    continue
                interwiki = self.countInterwiki(t)
                if self.getOption('test'):
                    pywikibot.output('INTERWIKI [[%s]]:%s' % (t,interwiki))

                self.wikichallenge['articles'][t] = {
                    'dayN':d, 
                    'day':days[d]['day'], 
                    'week':days[d]['week'], 
                    'author':u, 
                    'points':self.points(interwiki), 
                    'interwiki':interwiki,
                }

        if self.getOption('test'):
            pywikibot.output('WIKICHALLENGE')
            pywikibot.output(self.wikichallenge)

        self.resetCounters()
        self.countDayResults()
        self.countWeekResults()
        self.printSortedDays()
        self.countIncDayResults()
        self.printSortedIncDays()
        self.countPositions()

    def resetCounters(self):
        #reset all counters after getting info on articles
        self.wikichallenge['users'] = {}
        self.wikichallenge['weeks'] = {}
        self.wikichallenge['days'] = {}
        self.wikichallenge['incdays'] = {}
        self.wikichallenge['positions'] = {}

    def printSortedDays(self):
        for i in sorted(self.wikichallenge['days'].keys()):
            sorted_days = sorted(self.wikichallenge['days'][i].items(), key=operator.itemgetter(1), reverse=True)
            pywikibot.output('DAY %i:%s' % (i,sorted_days))

    def printSortedIncDays(self):
        for i in sorted(self.wikichallenge['incdays'].keys()):
            sorted_days = sorted(self.wikichallenge['incdays'][i].items(), key=operator.itemgetter(1), reverse=True)
            pywikibot.output('INCDAY %i:%s' % (i,sorted_days))


    def points(self,interwiki):
       # count point as min(iw^2,400)
       res = interwiki*interwiki
       if res>400:
           return(400)
       else:
           return(res)


    def countInterwiki(self,t):
        #count interwikis
        siteR = re.compile(ur'(?m)^(?P<site>.*)wiki$')
        if t in self.wikichallenge['articles'].keys():
            if self.getOption('test'):
                pywikibot.output('INTERWIKI EXISTING [[%s]]:%i' % (t,self.wikichallenge['articles'][t]['interwiki']))
            return(self.wikichallenge['articles'][t]['interwiki'])

        iw = []
        page = pywikibot.Page( pywikibot.Site(), t )
        while page.isRedirectPage():
            page = page.getRedirectTarget()
        try:
            d = page.data_item()
            pywikibot.output(u'WD: %s WIKI:%s' % (d.title(),page.title()) )
            dataItem = d.get()
            #pywikibot.output(u'DataItem:%s' % dataItem.keys()  )
            sitelinks = dataItem['sitelinks']
            if self.getOption('testiw'):
                pywikibot.output('SITELINKS:%s' % sitelinks)
            for s in sitelinks:
                site = siteR.match(s)
                if site:
                    if not site.group('site') in ['pl','commons']:
                        iw.append( s )
                        if self.getOption('testiw'):
                            pywikibot.output('SITELINKS adding site:%s' % s)

                #print( iw)
        except:
            pass
        return(len(iw))
        l = len(iw)
        if l:
            return(l-1)
        else:
            return(0)
    
    def getDays(self,text):
        #return list of day sections from text
        dayR = re.compile(ur'(?P<day>\n=+\s*?(?P<date>\d+\s*?(kwietnia|maja))\s*?=+(\n+#\s*?[^\n]*)*)')
        count = 0
        result = {}
        for d in dayR.finditer(text):
            count += 1
            dayNumber = self.dayToNumber(d.group('date'))
            result[dayNumber] = {}
            result[dayNumber]['day'] = d.group('date')
            result[dayNumber]['week'] = self.wikiweek(dayNumber)
            result[dayNumber]['body'] = d.group('day')

            if self.getOption('test'):
                pywikibot.output('======================================')
                pywikibot.output('=      Day %i = %s              =' % (count,d.group('date')))
                pywikibot.output('=      Day calc %i              =' % self.dayToNumber(d.group('date')))
                pywikibot.output('=      Week calc %i              =' % self.wikiweek(self.dayToNumber(d.group('date'))))
                pywikibot.output('======================================')
                pywikibot.output(d.group('day'))
        return(result)

    def getArtsUsers(self,text):
        #return list of (art,user)
        auR = re.compile(ur'#\s*?\[\[(?P<title>[^\|\]]*)\]\]\s*?[–-]\s*(?P<user>[^-\n]*)')
        count = 0
        result = []
        #pywikibot.output(text)
        for au in auR.finditer(text):
            count += 1
            #pywikibot.output('Art:[[%s]], User:%s' % (au.group('title'),au.group('user')))
            result.append((au.group('title'),au.group('user').strip()))
        return(result)

    def wikiweek(self,day):
        return(int((day-1)/6)+1)

    def dayToNumber(self,day):
        dtn = { '15 kwietnia':1, '16 kwietnia':2, '17 kwietnia':3, '18 kwietnia':4, '19 kwietnia':5, '20 kwietnia':6, '21 kwietnia':7, '22 kwietnia':8, '23 kwietnia':9, '24 kwietnia':10, '25 kwietnia':11, '26 kwietnia':12, '27 kwietnia':13, '28 kwietnia':14, '29 kwietnia':15, '30 kwietnia':16, '1 maja':17, '2 maja':18, '3 maja':19, '4 maja':20, '5 maja':21, '6 maja':22, '7 maja':23, '8 maja':24, '9 maja':25, '10 maja':26, '11 maja':27, '12 maja':28, '13 maja':29, '14 maja':30 }
        return(dtn[day])

    def numberToDay(self,num):
        ntd = { 1:'15 kwietnia', 2:'16 kwietnia', 3:'17 kwietnia', 4:'18 kwietnia', 5:'19 kwietnia', 6:'20 kwietnia', 7:'21 kwietnia', 8:'22 kwietnia', 9:'23 kwietnia', 10:'24 kwietnia', 11:'25 kwietnia', 12:'26 kwietnia', 13:'27 kwietnia', 14:'28 kwietnia', 15:'29 kwietnia', 16:'30 kwietnia', 17:'1 maja', 18:'2 maja', 19:'3 maja', 20:'4 maja', 21:'5 maja', 22:'6 maja', 23:'7 maja', 24:'8 maja', 25:'9 maja', 26:'10 maja', 27:'11 maja', 28:'12 maja', 29:'13 maja', 30:'14 maja' }
        return(ntd[num])

    def getInterwiki(self,page):
        # yield interwiki sites generator
        iw = []
        iwlinks = 0
        try:
            d = page.data_item()
            pywikibot.output(u'WD: %s' % d.title() )
            dataItem = d.get()
            #pywikibot.output(u'DataItem:%s' % dataItem.keys()  )
            sitelinks = dataItem['sitelinks']
            iwlinks = len(sitelinks)
            '''
            for s in sitelinks:
                #if self.getOption('test'):
                #    pywikibot.output(u'SL iw: %s' % d)
                site = re.sub(ur'(.*)wiki$', ur'\1',s)
                if site == u'be_x_old':
                    site = u'be-tarask'
                ssite = pywikibot.Site(site,fam='wikipedia')
                spage = pywikibot.Page( ssite, title=sitelinks[s] )
                #pywikibot.output(u'gI Page: %s' % spage.title(asLink=True,forceInterwiki=True) )
                iw.append( spage )
                #print( iw)
            '''
        except:
            pass
        #print(iw)
        return(iwlinks)

    def loadArticleList(self):
        #load article list form pickled dictionary
        #result = {}
        if self.getOption('reset'):
            if self.getOption('testpickle'):
                pywikibot.output('PICKLING SKIPPED at %s' % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        else:
            if self.getOption('testpickle'):
                pywikibot.output('PICKLING LOAD at %s' % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            try:
                with open('masti/wikiwyzwanie2018.dat', 'rb') as datfile:
                    self.wikichallenge = pickle.load(datfile)
            except (IOError, EOFError):
                # no saved history exists yet, or history dump broken
                if self.getOption('testpickle'):
                    pywikibot.output('PICKLING FILE NOT FOUND')
                #result = {}
        if self.getOption('testpickle'):
            pywikibot.output('PICKLING RESULT:%s' % self.wikichallenge)


    def pickleArticleList(self,artList):
        #save list as pickle file
        if self.getOption('testpickle'):
            pywikibot.output('PICKLING SAVE at %s' % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        with open('masti/wikiwyzwanie2018.dat', 'wb') as f:
            pickle.dump(artList, f, protocol=config.pickle_protocol)

    def saveArticleList(self, res, pagename, header, footer):
        # save article list at self.getOption('outpage')/list
        # generate table header

        finalpage = header
        finalpage += u'\n{| class="wikitable sortable" style="text-align: center;"'
        finalpage += u'\n|-'
        finalpage += u'\n! #'
        finalpage += u'\n! Artykuł'
        finalpage += u'\n! Autor'
        finalpage += u'\n! Dzień'
        finalpage += u'\n! Tydzień'
        finalpage += u'\n! Interwiki'
        finalpage += u'\n! Punkty'

        count = 0
        for a in res['articles'].keys():
            count += 1
            finalpage += u'\n|-\n|'
            finalpage += u'%i. || [[%s]] || [[Wikipedysta:%s|%s]] || %i (%s) || %i || %i || %i' % (count, a,
               res['articles'][a]['author'],
               res['articles'][a]['author'],
               res['articles'][a]['dayN'],
               res['articles'][a]['day'],
               res['articles'][a]['week'],
               res['articles'][a]['interwiki'],
               res['articles'][a]['points'] )


        finalpage += u'\n|}'
        finalpage += footer

        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if self.getOption('test'):
            pywikibot.output(u'ArticleList:%s' % outpage.title())
        outpage.text = finalpage
        outpage.save(summary=self.getOption('summary'))

        return

    def generateResultTable(self, res, pagename, header, footer):
        #generate main results page sorted daily 

        finalpage = header
        incDays = res['incdays']
        if self.getOption('test'):
            pywikibot.output('RESULT:%s' % incDays)

        finalpage += '\n== Wyniki dzienne =='
        for i in sorted(incDays.keys(),reverse=True):
            finalpage += '\n=== %s (dzień %i.) ===' % (self.numberToDay(i), i)
            count = 0
            finalpage += u'\n{| class="wikitable sortable" style="text-align: center;"'
            finalpage += u'\n|-'
            finalpage += u'\n! #'
            finalpage += u'\n! Zmiana'
            finalpage += u'\n! Autor'
            finalpage += u'\n! Punkty'
            for u,p in sorted(incDays[i].items(), key=operator.itemgetter(1), reverse=True):
                count += 1
                finalpage += u'\n|-\n| '
                finalpage += '%i. || %s || [[Wikipedysta:%s|%s]] || %i' % (res['positions'][i][u], self.posDiff(u,i), u, u, p)
            finalpage += u'\n|}'


        weeks = res['weeks']
        if self.getOption('test'):
            pywikibot.output('RESULT:%s' % weeks)

        finalpage += '\n== Wyniki konkursów 6-dniowych =='
        for i in sorted(weeks.keys(),reverse=True):
            finalpage += '\n=== Konkurs %i. (%s - %s) dzień %i. ===' % (i,self.numberToDay(i*6-5),self.numberToDay(i*6)) 
            count = 0
            finalpage += u'\n{| class="wikitable sortable" style="text-align: center;"'
            finalpage += u'\n|-'
            finalpage += u'\n! #'
            finalpage += u'\n! Autor'
            finalpage += u'\n! Punkty'
            for u,p in sorted(weeks[i].items(), key=operator.itemgetter(1), reverse=True):
                count += 1
                finalpage += u'\n|-\n| '
                finalpage += '%i. || [[Wikipedysta:%s|%s]] || %i' % (count, u, u, p)
            finalpage += u'\n|}'

        finalpage += footer

        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if self.getOption('test'):
            pywikibot.output(u'ArticleList:%s' % outpage.title())
        outpage.text = finalpage
        outpage.save(summary=self.getOption('summary'))

    def countIncDayResults(self):
        #count result incrementaly
        if self.getOption('testinc'):
            pywikibot.output('countIncDayResults')
        for i in sorted(self.wikichallenge['days'].keys()):
            if self.getOption('testinc'):
                pywikibot.output('incDays: i:%s' % i)
            self.wikichallenge['incdays'][i] = {}
            if i > 1:
                currDay = sorted(self.wikichallenge['days'][i].items(), key=operator.itemgetter(1))
                prevDay = sorted(self.wikichallenge['incdays'][i-1].items(), key=operator.itemgetter(1))
                if self.getOption('testinc'):
                    pywikibot.output('incDays CURR day:%s' % currDay) 
                    pywikibot.output('incDays PREV day:%s' % prevDay)
                for u,p in prevDay:
                    if self.getOption('testinc'):
                        pywikibot.output('incDays prevday: i:%s<>%s' % (u,p))
                    self.wikichallenge['incdays'][i][u] = p
                for u,p in currDay:
                    if u in self.wikichallenge['incdays'][i].keys():
                        if self.getOption('testinc'):
                            pywikibot.output('incDays adding: %s=%i+%i' % (u,self.wikichallenge['incdays'][i][u],p))
                        self.wikichallenge['incdays'][i][u] += p
                    else:
                        if self.getOption('testinc'):
                            pywikibot.output('incDays setting: %s=%i' % (u,p))
                        self.wikichallenge['incdays'][i][u] = p
            else:
                currDay = sorted(self.wikichallenge['days'][i].items(), key=operator.itemgetter(1))
                if self.getOption('testinc'):
                    pywikibot.output('incDays1 CURR day:%s' % currDay) 
                for u,p in currDay:
                    if self.getOption('testinc'):
                        pywikibot.output('incDays setting: %s=%i' % (u,p))
                    self.wikichallenge['incdays'][i][u] = p
                
        if self.getOption('testincdays'):
            pywikibot.output('CHALLENGE INCDAYS:%s' % self.wikichallenge['incdays'])
          
    def countDayResults(self):
        #count result per each day
        for a in self.wikichallenge['articles'].keys():
            currArt = self.wikichallenge['articles'][a]
            currArtN = currArt['dayN']
            points = currArt['points']
            if not currArt['dayN'] in self.wikichallenge['days'].keys():
                self.wikichallenge['days'][currArtN] = {}
            if currArt['author'] in self.wikichallenge['days'][currArtN].keys():
                self.wikichallenge['days'][currArtN][currArt['author']] += points
            else:
                self.wikichallenge['days'][currArtN][currArt['author']] = points
        if self.getOption('testdays'):
            pywikibot.output('CHALLENGE DAYS:%s' % self.wikichallenge['days'])

    def countWeekResults(self):
        #count result per each day
        for a in self.wikichallenge['articles'].keys():
            currArt = self.wikichallenge['articles'][a]
            currArtN = currArt['week']
            if not currArt['week'] in self.wikichallenge['weeks'].keys():
                self.wikichallenge['weeks'][currArtN] = {}
            if currArt['author'] in self.wikichallenge['weeks'][currArtN].keys():
                self.wikichallenge['weeks'][currArtN][currArt['author']] += currArt['points']
            else:
                self.wikichallenge['weeks'][currArtN][currArt['author']] = currArt['points']
        if self.getOption('testweeks'):
            pywikibot.output('CHALLENGE WEEKS:%s' % self.wikichallenge['weeks'])

    def countPositions(self):
        #count user positions in contest
        days = self.wikichallenge['incdays']
        for d in days.keys():
            results = days[d]
            if self.getOption('testchange'):
                pywikibot.output('POS RESULTS:%s' % results)
            positions = sorted(results.items(), key=operator.itemgetter(1), reverse=True)
            if self.getOption('testchange'):
                pywikibot.output('POSITIONS:%s' % positions)
            count = 0
            self.wikichallenge['positions'][d] = {}
            pos = self.wikichallenge['positions'][d]
            for u,p in positions:
                if not count:
                    count += 1
                    pos[u] = count
                    oldpoints = p
                    oldcount = count
                else:
                    count += 1
                    if p == oldpoints:
                        pos[u] = oldcount
                    else:
                        pos[u] = count
                        oldpoints = p
                        oldcount = count
            if self.getOption('testchange'):
                pywikibot.output('POSITIONS CALCULATED:%s' % sorted(pos.items(), key=operator.itemgetter(1)))

    def posDiff(self,user,currday):
        #calculate change position in user position
        # return {{zmiana|wzrost|2}} or '''N'''
        prevday = currday - 1
        if not prevday:
            return("'''N'''")
        pday = self.wikichallenge['positions'][prevday]
        cday = self.wikichallenge['positions'][currday]
        if user in pday.keys():
            diff = pday[user] - cday[user]
            if diff < 0:
               return('{{zmiana|spadek}} %i' % diff)
            elif diff > 0:
               return('{{zmiana|wzrost}} +%i' % diff)
            else:
               return('{{zmiana|stagnacja}}')
        else:
            return("'''N'''")
                       


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
