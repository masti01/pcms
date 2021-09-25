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
-multi:           return all results for -regex not only first match
-flags:           list of regex flags: i,m,g,s etc.
-edit:            link thru template:edytuj instead of wikilink
-cite:            cite search results
-nowiki:          put citation in <nowiki> tags
-navi:            add navigation template {{Wikipedysta:MastiBot/Nawigacja|Wikipedysta:mastiBot/test|Wikipedysta:mastiBot/test 2}}
-progress:        report progress
-table:           present results in table
-nonempty:        show nonempty results only
-nodisabled:      remove disabled parts as per textlib.py
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
import datetime
from pywikibot import textlib

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
            'aslink': False, #put links as wikilinks
            'append': False, #append results to page
            'section': None, #section title
            'title': False, #check in title not text
            'multi': False, #'^' and '$' will now match begin and end of each line.
            'flags': None, #list of regex flags
            'edit': False, #link thru template:edytuj instead of wikilink
            'cite': False, #cite search results
            'nowiki': False, #put citation in <nowiki> tags
            'count': False, #count pages only
            'navi': False, # add navigation template
            'progress': False, # report progress
            'table': False, #present results in a table
            'nonempty': False, #show nonempty results only
            'talk': False, #check on talk page
            'nodisabled': False, #remove disabled parts as per textlib.py
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

        if not self.getOption('append'):
            if self.getOption('table'):
                header = u"Ostatnia aktualizacja: '''<onlyinclude>{{#time: Y-m-d H:i|{{REVISIONTIMESTAMP}}}}</onlyinclude>'''."
                header += u"\n\nWszelkie uwagi proszę zgłaszać w [[User talk:masti|dyskusji operatora]]."
                if self.getOption('regex'):
                    header += '\n\nregex: <code><nowiki>\'%s\'</nowiki></code>\n' % self.getOption('text')
                header +=u'\n{| class="wikitable sortable" style="font-size:85%;"'
                header +=u'\n|-'
                header +=u'\n!Nr'
                header +=u'\n!Artykuł'
                header +=u'\n!Wyniki'
            else:
                header = u"Ostatnia aktualizacja: '''<onlyinclude>{{#time: Y-m-d H:i|{{REVISIONTIMESTAMP}}}}</onlyinclude>'''.\n\n"
                header += u"Wszelkie uwagi proszę zgłaszać w [[User talk:masti|dyskusji operatora]].\n\n"
                if self.getOption('regex'):
                    header += '\n\nregex: <code><nowiki>\'%s\'</nowiki></code>\n' % self.getOption('text')
        else:
            header = u'\n\n'
        
        reflinks = [] #initiate list
        pagecounter = 0
        duplicates = 0
        marked = 0
        for page in self.generator:
            pagecounter += 1
            if self.getOption('test') or self.getOption('progress'):
                pywikibot.output(u'[%s] Treating #%i (marked:%i, duplicates:%i): %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),pagecounter, marked, duplicates, page.title()))
            if page.title() in reflinks:
                duplicates += 1
                continue
            refs = self.treat(page) # get (name)
            if refs:
                if not refs in reflinks:
                    #test
                    if self.getOption('test'):
                        pywikibot.output(refs)
                    reflinks.append(refs)
                    marked += 1
                else:
                    #test
                    if self.getOption('test'):
                        pywikibot.output(u'Already marked')

        footer = u'\n\nPrzetworzono ' + str(pagecounter) + u' stron.'

        outputpage = self.getOption('outpage')

        result = self.generateresultspage(reflinks,outputpage,header,footer)
        

    def generateresultspage(self, redirlist, pagename, header, footer):
        """
        Generates results page from redirlist
        Starting with header, ending with footer
        Output page is pagename + pagenumber split at maxlines rows
        """
        #finalpage = header
        finalpage = u''
        if self.getOption('section'):
            finalpage += u'== ' + self.getOption('section') + u' ==\n'
        #res = sorted(redirlist, key=redirlist.__getitem__, reverse=False)
        res = sorted(redirlist)
        itemcount = 0
        totalcount = len(res)
        pagecount = 0

        if self.getOption('count'):
            self.savepart(finalpage,pagename,pagecount,header,self.generateprefooter(pagename,totalcount,pagecount)+footer)
            return(1)
        
        for i in res:
            if self.getOption('regex') and not self.getOption('negative'):
                title, link = i
            else:
                title = i
            #finalpage += u'\n# [[' + title + u']]'
            linenumber = str(pagecount * int(self.getOption('maxlines')) + itemcount + 1) + u'.'
            if self.getOption('table'):
                finalpage += u'\n|-\n| %s || ' % linenumber
                if self.getOption('edit'):
                    nakedtitle = re.sub(r'\[\[|\]\]',u'',title)
                    finalpage += u'{{Edytuj|%s|%s}}' % ( nakedtitle,nakedtitle)
                else:
                    finalpage += re.sub(r'\[\[',u'[[:',title, count=1)
                finalpage += u' || '
            else:
                if self.getOption('edit'):
                    nakedtitle = re.sub(r'\[\[|\]\]',u'',title)
                    finalpage += u'\n:' + linenumber + ' {{Edytuj|' + nakedtitle + u'|' + nakedtitle + u'}}' 
                else:
                    finalpage += u'\n:' + linenumber + u' ' + re.sub(r'\[\[',u'[[:',title, count=1)
            if self.getOption('regex') and self.getOption('cite') and not self.getOption('negative'):
                if self.getOption('multi'):
                    #results are list
                    if self.getOption('nowiki'):
                        if self.getOption('table'):
                            for r in link:
                                finalpage += u'<nowiki>%s</nowiki><br />' % r
                        else:
                            finalpage += u' – <nowiki>' + ', '.join(link) + u'</nowiki><br />'
                else:
                    #results are single string
                    #TODO convert all results to lists
                    if self.getOption('nowiki'):
                        finalpage += u' – <nowiki>' + link + u'</nowiki>' if not self.getOption('table') else u'<nowiki>' + link + u'</nowiki>'
                    else:
                        finalpage += u' – ' + link if not self.getOption('table') else link
            itemcount += 1

            if itemcount > int(self.getOption('maxlines'))-1:
                pywikibot.output(u'***** saving partial results *****')
                self.savepart(finalpage,pagename,pagecount,header,self.generateprefooter(pagename,totalcount,pagecount)+footer)
                finalpage = u''
                itemcount = 0
                pagecount += 1

        #save remaining results
        pywikibot.output(u'***** saving remaining results *****')
        self.savepart(finalpage,pagename,pagecount,header,self.generateprefooter(pagename,totalcount,pagecount)+footer)


        return(pagecount)

    def generateprefooter(self,pagename, totalcount, pagecount):
        # generate text to appear before footer

        if self.getOption('test'):
            pywikibot.output(u'***** GENERATING PREFOOTER page '+ pagename + u' ' + str(pagecount) + u' *****')
        result = u''

        if self.getOption('table'):
            result += u'\n|}'
        # if no results found to be reported
        if not totalcount:
            result += u"\n\n'''Brak wyników'''\n\n"
        elif self.getOption('count'):
            result += u"\n\n'''Liczba stron spełniających warunki: " + str(totalcount) + u"'''"
        else:
            result += u"\n\n"

        return(result)

    def navigation(self,pagename, pagecount):
        #generate navigation template
        if pagecount > 1:
            result = u'\n\n{{User:mastiBot/Nawigacja|' + pagename + u' ' + str(pagecount-1) + u'|' + pagename + u' ' + str(pagecount+1) + u'}}\n\n'
        elif pagecount:
            result = u'\n\n{{User:mastiBot/Nawigacja|' + pagename + u'|' + pagename + u' ' + str(pagecount+1) + u'}}\n\n'
        else:
            result = u'\n\n{{User:mastiBot/Nawigacja|' + pagename + u'|' + pagename + u' ' + str(pagecount+1) + u'}}\n\n'
        return(result)
        

    def savepart(self, pagepart, pagename, pagecount, header, footer):
        # generate resulting page
        if self.getOption('test'):
            pywikibot.output('***** SAVING PAGE #%i' % pagecount) 
            #pywikibot.output(finalpage)

        if self.getOption('navi'):
            finalpage = self.navigation(pagename,pagecount) + header + pagepart + footer + self.navigation(pagename,pagecount) 
        else:
            finalpage = header + pagepart + footer

        if pagecount: 
            numberedpage = pagename + u' ' + str(pagecount)
        else:
            numberedpage = pagename

        outpage = pywikibot.Page(pywikibot.Site(), numberedpage)

        if self.getOption('append'):
            outpage.text += finalpage
        else:
            outpage.text = finalpage

        if self.getOption('test'):
            pywikibot.output(outpage.title())
            pywikibot.output(outpage.text)
        
        success = outpage.save(summary=self.getOption('summary'))
        #if not outpage.save(finalpage, outpage, self.summary):
        #   pywikibot.output(u'Page %s not saved.' % outpage.title(asLink=True))
        #   success = False
        return(success)
 
    def treat(self, cpage):
        """
        Returns page title if param 'text' not in page
        """

        if self.getOption('talk'):
            page = cpage.toggleTalkPage()
        else:
            page = cpage


        #choose proper source - title or text
        if self.getOption('title'):
            source = page.title()
        else:
            source = page.text

        if self.getOption('nodisable'):
            source = textlib.removeDisabledParts(source)

        # new version
        if self.getOption('regex'):
            if u'?P<result>' in self.getOption('text'):
                resultR =  self.getOption('text')
            else:
                resultR = u'(?P<result>' + self.getOption('text') + u')'
            if self.getOption('flags'):
                resultR = u'(?' + self.getOption('flags') + u')' + resultR

            if self.getOption('test'):
                pywikibot.output(resultR)
            resultR = re.compile(resultR)

            match = resultR.search(source)

            if not match and self.getOption('negative'):
                return(cpage.title(asLink=True,forceInterwiki=True, textlink=True))
            elif match and not self.getOption('negative'):
                if self.getOption('multi'):
                    #return all found results
                    resultslist = []
                    for r in re.finditer(resultR,source):
                        #based on nonempty
                        if (self.getOption("nonempty") and len(r.group('result').strip())) or not self.getOption("nonempty"):
                            resultslist.append(r.group('result'))
                    return(cpage.title(asLink=True,forceInterwiki=True, textlink=True),resultslist)
                else:
                    #return just first match
                    #based on nonempty
                    if (self.getOption("nonempty") and len(match.group('result').strip())) or not self.getOption("nonempty"):
                        return(cpage.title(asLink=True,forceInterwiki=True, textlink=True),match.group('result'))
            return(None)
            
        else:  
            isIn = self.getOption('text') in source
            if not isIn and self.getOption('negative'):
                if self.getOption('test'):
                    pywikibot.output('NEGATIVE:Text not found')
                return(cpage.title(asLink=True,forceInterwiki=True, textlink=True))
            if isIn and not self.getOption('negative'):
                if self.getOption('test'):
                    pywikibot.output('POSITIVE:Text found')
                return(cpage.title(asLink=True,forceInterwiki=True, textlink=True))
            return(None)

    def listargs(self):
        #return list of arguments
        pywikibot.output(options)

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
        if option in ('summary', 'text', 'outpage', 'maxlines', 'section','flags'):
            if not value:
                pywikibot.input('Please enter a value for ' + arg)
            options[option] = value
        # take the remaining options as booleans.
        # You will get a hint if they aren't pre-definded in your bot class
        else:
            options[option] = True

    pywikibot.output(options)
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
