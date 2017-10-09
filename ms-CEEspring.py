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

-negative:        mark if text not in page

-v:               make verbose output
-vv:              make even more verbose output

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
    springList = {}
    templatesList = {}
    authors = {}
    missingCount = {}
    pagesCount = {}
    women = {'pl':0, 'az':0, 'ba':0, 'be':0, 'be-tarask':0, 'bg':0, 'de':0, 'crh':0, 'el':0, 'myv':0, 'eo':0, 'hy':0, 'ka':0, 'lv':0, 'lt':0, \
             'mk':0, 'ro':0, 'ru':0, 'sq':0, 'sr':0, 'tt':0, 'tr':0, 'uk':0}
    countryp = { 'pl':'kraj', 'az':'ölkə', 'ba':'ил', 'be':'краіна', 'Be-tarask':'краіна', 'bg':'държава', 'de':'land', 'crh':'memleket', 'el':'country', \
                 'myv':'мастор', 'eo':'country', 'ka':'ქვეყანა', 'lv':'valsts', 'lt':'šalis', 'mk':'земја', 'ro':'țară', 'ru':'страна', 'sq':'country', \
                 'sr':'држава', 'tt':'ил', 'tr':'ülke', 'uk':'країна' }
    topicp = {'pl':'parametr', 'az':'qadınlar', 'ba':'тема', 'be':'тэма', 'Be-tarask':'тэма', 'bg':'тема', 'de':'thema', 'crh':'mevzu', 'el':'topic', \
             'myv':'тема', 'eo':'topic', 'ka':'თემა', 'lv':'tēma', 'lt':'tema', 'mk':'тема', 'ro':'subiect', 'ru':'тема', 'sq':'topic', 'sr':'тема', \
             'tt':'тема', 'tr':'konu', 'uk':'тема'}
    womenp = {'pl':'kobiety', 'az':'qadınlar', 'ba':'Ҡатын-ҡыҙҙар', 'be':'Жанчыны', 'Be-tarask':'жанчыны', 'bg':'жени', 'de':'Frauen', 'el':'γυναίκες', \
              'ka':'ქალები', 'lv':'Sievietes', 'mk':'Жени', 'ro':'Femei', 'ru':'женщины', 'sq':'Gratë', 'sr':'Жене', 'tt':'Хатын-кызлар', 'tr':'Kadın', 'uk':'жінки'}
    

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
            'testprint': False, # print testoutput
            'negative': False, #if True negate behavior i.e. mark pages that DO NOT contain search string
            'test': False, # make verbose output
            'append': False, 

        })

        # call constructor of the super class
        #super(BasicBot, self).__init__(site=True, **kwargs)
        super(BasicBot, self).__init__(**kwargs)

        # assign the generator to the bot
        self.generator = generator

        # get the template list
        #self.springList = self._getSpringList()

    def run(self):

        header = u"last update: '''<onlyinclude>{{#time: Y-m-d H:i|{{REVISIONTIMESTAMP}}}}</onlyinclude>'''.\n\n"
        footer = u''

        #get template interwikis
        for p in self.generator:
            #p = t.toggleTalkPage()
            pywikibot.output(u'Treating: %s' % p.title())
            d = p.data_item()
            pywikibot.output(u'WD: %s' % d.title() )
            dataItem = d.get()
 
            for i in self.genInterwiki(p):
                lang = self.lang(i.title(asLink=True,forceInterwiki=True))
                #if lang not in ('be','pl'):
                #    continue
                self.templatesList[lang] = i.title()
                pywikibot.output(u'Getting references to %s Lang:%s' % (i.title(asLink=True,forceInterwiki=True), lang) )
                count = 0
                missing = 0
                articles = {}
                for p in i.getReferences(namespaces=1):
                    artParams = {}
                    art = p.toggleTalkPage()
                    count += 1
                    if art.exists():
                        #creator, creationDate = art.getCreator()
                        #pywikibot.output(u'%i:%s (Auth:%s, Created:%s)' % (count, art.title(asLink=True,forceInterwiki=True),creator, creationDate))
                        #count += 1
                        TmplInfo = self.getTemplateInfo(p, i.title(),lang)
                        creator, creationDate = art.getCreator()

                        artParams['template'] = TmplInfo
                        artParams['creator'] = creator
                        artParams['creationDate'] = creationDate
                        #print artParams

                        articles[art.title()] = artParams

                        author = u'[[:' + lang + u':user:' + creator + u'|' + lang + u':' + creator + u']]'

                        if creator in self.authors.keys():
                            self.authors[creator] +=1
                        else:
                            self.authors[creator] =1
                        #print (TmplInfo)
                    else:
                        missing += 1
                        pywikibot.output(u'Article referenced does not exist')
                self.springList[lang] = articles
                self.missingCount[lang] = missing
                self.pagesCount[lang] = count

                print(self.springList)
                print(self.authors)
                print(self.missingCount)
                print(self.pagesCount)
                print(self.women)

        self.generateresultspage(self.springList,self.getOption('outpage'),header,footer)
        return

    def getTemplateInfo(self,page,template,lang):
        param = {}
        #return dictionary with template params
        for t in page.templatesWithParams():
            title, params = t
            #print(title)
            #print(params)
            tt = re.sub(ur'\[\[.*?:(.*?)\]\]', r'\1', title.title())
            if self.getOption('test'):
                pywikibot.output(u'tml:%s = %s' % (title,template) )
            if tt == template:
                paramcount = 1
                for p in params:
                    named, name, value = self.templateArg(p)
                    if not named:
                        name = str(paramcount)
                    param[name] = value
                    paramcount += 1
                    if self.getOption('test'):
                        pywikibot.output(u'p:%s' % p )
                    #check parameter type: country, topic
                    if lang in self.topicp.keys() and name.lower().startswith(self.topicp[lang].lower()):
                        if self.getOption('test'):
                            pywikibot.output(u'topic:%s:%s' % (name,value))
                        if lang in self.womenp.keys() and value.lower().startswith(self.womenp[lang].lower()):
                            self.women[lang] += 1
                    if lang in self.countryp.keys() and name.lower().startswith(self.countryp[lang].lower()):
                        if self.getOption('test'):
                            pywikibot.output(u'country:%s:%s' % (name,value))
                return param
        return param

    def lang(self,template):
        return(re.sub(ur'\[\[(.*?):.*?\]\]',ur'\1',template))

    def genInterwiki(self,page):
        # yield interwiki sites generator
        iw = []
        try:
            d = page.data_item()
            pywikibot.output(u'WD: %s' % d.title() )
            dataItem = d.get()
            #pywikibot.output(u'DataItem:%s' % dataItem.keys()  )
            sitelinks = dataItem['sitelinks']
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
        except:
            pass
        #print(iw)
        return(iw)

    def _getSpringList(self):
        if self.getOption('test'):
            pywikibot.output(u'getSpringList')
        
        iwlist = ()
        CEESrpingTpml = pywikibot.Page(pywikibot.Site(), u'Szablon:CEE Spring 2017')
        pywikibot.output(CEESrpingTpml.title(asLink=True,forceInterwiki=True))
        tmpl = CEESrpingTpml.data_item().get()
        pywikibot.output(tmpl['sitelinks'])
        for i in tmpl['sitelinks']:
            iw,t = i
            if self.getOption('test'):
                #pywikibot.output(i.title(forceInterwiki=True))
                pywikibot.output(u'Iw:%s,Title:%s' % (iw,t))
            #iwlist.append(i.title(forceInterwiki=True))
        return(iwlist)

    def generateresultspage(self, res, pagename, header, footer):
        """
        Generates results page from redirlist
        Starting with header, ending with footer
        Output page is pagename
        """

        finalpage = header

        itemcount = 0
        for i in res.keys():
            count = 1
            #print('[[:' + i + u':' + self.templatesList[i] +u'|' + i + u' wikipedia]]')
            finalpage += u'\n== [[:' + i + u':' + self.templatesList[i] +u'|' + i + u' wikipedia]] ==\n\n'
            finalpage += u'Counted: ' + str(self.pagesCount[i]) + u' Missing:' + str(self.missingCount[i]) + u'\n\n'
            wiki = res[i]
            #print(wiki)
            for a in wiki.keys():
                finalpage += u'\n# [[:' + i + u':' + a + u']] - user:' + wiki[a]['creator'] + u' date:' + wiki[a]['creationDate']
                '''
                tmpl = wiki[a]['template']
                for p in tmpl.keys():
                    #print(p)
                    #print(tmpl[p])
                    finalpage += u',' + p + u'='
                    if tmpl[p]:
                        finalpage += tmpl[p]
                '''

        finalpage += u'\n== Authors ==\n'
        #ath = sorted(self.authors, reverse=True)
        ath = sorted(self.authors, key=self.authors.__getitem__, reverse=True)
        for a in ath:
             finalpage += u'\n# ' + a + u' - ' + str(self.authors[a])

        finalpage += u'\n== Articles about women ==\n'
        #ath = sorted(self.authors, reverse=True)
        wom = sorted(self.women, key=self.women.__getitem__, reverse=True)
        for a in self.women:
             finalpage += u'\n# ' + a + u' - ' + str(self.women[a])


        finalpage += footer 

        #pywikibot.output(finalpage)
        success = True
        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if self.getOption('append'):
            outpage.text += finalpage
        else:
            outpage.text = finalpage

        pywikibot.output(outpage.title())
        
        outpage.save(summary=self.getOption('summary'))
        #if not outpage.save(finalpage, outpage, self.summary):
        #   pywikibot.output(u'Page %s not saved.' % outpage.title(asLink=True))
        #   success = False
        return(success)


    def treat_page(self):
        """Load the given page, do some changes, and save it."""
        text = self.current_page.text

        ################################################################
        # NOTE: Here you can modify the text in whatever way you want. #
        ################################################################

        # If you find out that you do not want to edit this page, just return.
        # Example: This puts Text on a page.

        # Retrieve your private option
        # Use your own text or use the default 'Test'
        text_to_add = self.getOption('text')

        if self.getOption('replace'):
            # replace the page text
            text = text_to_add

        elif self.getOption('top'):
            # put text on top
            text = text_to_add + text

        else:
            # put text on bottom
            text += text_to_add

        # if summary option is None, it takes the default i18n summary from
        # i18n subdirectory with summary_key as summary key.
        self.put_current(text, summary=self.getOption('summary'))

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
        if self.getOption('test'):
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
