#!/usr/bin/python
# -*- coding: utf-8 -*-
"""

Use global -simulate option for test purposes. No changes to live wiki
will be done.

Call: 
	python pwb.py m-tematicweek.py -page:"Wikiprojekt:Tygodnie tematyczne/Tydzień Artykułu Bhutańskiego" -pt:0 -log:"Tydzień Artykułu Bhutańskiego"

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
            'testprint': False, # print testoutput
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

        # set up log page and load
	logpage = pywikibot.Page(pywikibot.Site(), u'Wikipedysta:MastiBot/Tygodnie Tematyczne/zrobione')
        if not logpage.text:
            return

        for page in self.generator:
            if self.treat_page(page):
                logpage.text += u'\n# [[' + page.title() + u']] --~~~~~'

        #pywikibot.output(logpage.text)
        logpage.save(summary=u'Tygodnie Tematyczne: log')


    def treat_page(self, page):
        """Load the given page, retrieve links to updated pages. Add template to talkpage if necessary"""

        text = page.text
	# get template for marking articles
	t = re.search(ur'(?P<templatename>{{Wikiprojekt:Tygodnie tematyczne/info.*?}})',text)
        if not t:
            pywikibot.output(u'Template not found!')
            return(False)

	templatename = t.group('templatename')
	pywikibot.output(u'Template:%s' % templatename)

	# set summary for edits
	summary = u'Bot dodaje szablon ' + templatename

        #get articlenames to work on
	#get article section
	t = re.search(ur'(?P<articlesection>=== Lista alfabetyczna.*?)== ',text,re.DOTALL)
	articlesection = t.group('articlesection')
	#pywikibot.output(u'Articles:%s' % articlesection)

	Rlink = re.compile(r'\[\[(?P<title>[^\]\|\[]*)(\|[^\]]*)?\]\]')

	for match in Rlink.finditer(articlesection):
            title = match.group('title')
            title = title.replace("_", " ").strip(" ")
	    #pywikibot.output(u'Art:[[%s]]' % title)
            artpage = pywikibot.Page(pywikibot.Site(), title)

            # follow redirects
            while artpage.isRedirectPage():
                oldtitle = artpage.title()
                artpage = artpage.getRedirectTarget()
                pywikibot.output(u'Art:[[%s]] FOLLOWING REDIR TO:%s' % (oldtitle, artpage.title()))

            #check if article exists
            if not (artpage.namespace() in [0,10,14]):
                pywikibot.output(u'Art:[[%s]] SKIPPED:wrong namespace' % artpage.title())
                continue
            elif artpage.exists():
                workpage = artpage.toggleTalkPage()
            else:
                pywikibot.output(u'Art:[[%s]] DOES NOT EXIST' % artpage.title())
                continue
	    #pywikibot.output(u'Art:[[%s]]>>>[[%s]]' % (title,workpage.title()))
            #load discussion Page
	    worktext = workpage.text
            if worktext:
	        #check if template exists
                if u'{{Wikiprojekt:Tygodnie tematyczne/info' in worktext:
	            pywikibot.output(u'Art:[[%s]] not changed: template found' % workpage.title())
                    continue
	        else:
                    pywikibot.output(u'Art:[[%s]] changed: template added' % workpage.title())
                    worktext = templatename + u'\n' + worktext
            else:
                pywikibot.output(u'Art:[[%s]] created' % workpage.title())
                worktext = templatename
            
            workpage.text = worktext
            workpage.save(summary=self.getOption('summary'))


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
