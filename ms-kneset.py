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
	python pwb.py masti/ms-kneset.py -transcludes:Kneset -outpage:"Wikipedysta:Andrzei111/Izrael/lista" -maxlines:10000 -ns:0 -summary:"Bot uaktualnia tabelę"

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
        header +=u'\n{| class="wikitable sortable" style="font-size:85%;"'
        header +=u'\n|-'
        header +=u'\n!Nr'
        header +=u'\n!Id'
        header +=u'\n!Link Kneset'
        header +=u'\n!Polityk'
        header +=u'\n!Autor'
        header +=u'\n!Data modyfikacji'


        reflinks = [] #initiate list
        licznik = 0
        for tpage in self.generator:
	    licznik += 1
            pywikibot.output(u'Treating #%i: %s' % (licznik, tpage.title()))
            refs = self.treat(tpage) # get (name, id, creator, lastedit)
            pywikibot.output(refs)
            reflinks.append(refs)

        footer = u'\n|}'
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

            title, ident, name, creator, lastedit = i

            if (not name) or (name == title):
                itemcount += 1

                finalpage += u'\n|-\n| ' + str(itemcount) + u' || ' + ident + u' || '
                finalpage += u'{{Kneset|' + ident + u'|name='
                if name:
                    finalpage += name
                else:
                    finalpage += title
                #finalpage += u'}} || [[' + title + u']] || [[Wikipedysta:' + creator + u'|' + creator + u']] || ' + str(datetime.datetime.strptime(str(lastedit), "%Y%m%d%H%M%S"))
                finalpage += u'}} || [[' + title + u']] || [[Wikipedysta:' + creator + u'|' + creator + u']] || ' + str(lastedit)

                if itemcount > maxlines-1:
                    pywikibot.output(u'*** Breaking output loop ***')
                    break
            else:
                pywikibot.output(u'SKIPPING')

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
 
    def treat(self, tpage):
        """
        Creates a tuple (title, id, name, creator, lastedit)
        """
        found = False
        rowtext = u''
	
        # check for id & name(optional)
        for t in tpage.templatesWithParams():
            (tTitle,paramList) = t
            #test
            #pywikibot.output(u'Template:%s' % tTitle)
            if u'Kneset' in tTitle.title():
                name = None
                ident = None
                for p in paramList:
                    pywikibot.output(u'param:%s' % p)
                    pnamed, pname, pvalue = templateArg(p)
                    if pnamed:
                        if pname.startswith('name'):
                            name = pvalue
                    else:
                        ident = pvalue
                        #pywikibot.output(u'ident:%s' % ident)

        # check for page creator
        #creator, timestamp = tpage.getCreator()
        creator = tpage.oldest_revision.user
        timestamp = unicode(tpage.oldest_revision.timestamp.isoformat())
        #test
        pywikibot.output(u'Creator:%s<<Timestamp %s' % (creator, timestamp))

        # check for last edit
        lastedit = tpage.editTime()
        #test
        pywikibot.output(u'lastedit:%s' % lastedit)
        pywikibot.output(u'ident:%s' % ident)
         
        return(tpage.title(),ident,name,creator,lastedit)

def templateArg(param):
        """
        return name,value for each template param

        input text in form "name = value"
        @return: a tuple for each param of a template
            named: named (True) or int
            name: name of param or None if numbered
            value: value of param
        @rtype: tuple
        """
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
