#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An incomplete sample script.

This is a bot to create list of articles about women from pagegenerator

Use global -simulate option for test purposes. No changes to live wiki
will be done.


The following parameters are supported:

-always           The bot won't ask for confirmation when putting a page

-text:            Use this text to be added; otherwise 'Test' is used

-replace:         Don't add text but replace it

-top              Place additional text on top of the page

-summary:         Set the action summary message for the edit.

All settings can be made either by giving option with the command line
or with a settings file which is scripts.ini by default. If you don't
want the default values you can add any option you want to change to
that settings file below the [basic] section like:

    [basic] ; inline comments starts with colon
    # This is a commend line. Assignments may be done with '=' or ':'
    text: A text with line break and
        continuing on next line to be put
    replace: yes ; yes/no, on/off, true/false and 1/0 is also valid
    summary = Bot: My first test edit with pywikibot

Every script has its own section with the script name as header.

In addition the following generators and filters are supported but
cannot be set by settings file:

&params;
"""
#
# (C) Pywikibot team, 2006-2020
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import pagegenerators

from pywikibot.bot import (
    SingleSiteBot, ConfigParserBot, ExistingPageBot, NoRedirectPageBot,
    AutomaticTWSummaryBot)
from pywikibot.tools import PYTHON_VERSION

if PYTHON_VERSION >= (3, 9):
    Tuple = tuple
else:
    from typing import Tuple
import datetime

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class BasicBot(
    # Refer pywikobot.bot for generic bot classes
    SingleSiteBot,  # A bot only working on one site
    ConfigParserBot,  # A bot which reads options from scripts.ini setting file
    # CurrentPageBot,  # Sets 'current_page'. Process it in treat_page method.
    #                  # Not needed here because we have subclasses
    ExistingPageBot,  # CurrentPageBot which only treats existing pages
    NoRedirectPageBot,  # CurrentPageBot which only treats non-redirects
    AutomaticTWSummaryBot,  # Automatically defines summary; needs summary_key
):
    """
    An incomplete sample bot.

    @ivar summary_key: Edit summary message key. The message that should be
        used is placed on /i18n subdirectory. The file containing these
        messages should have the same name as the caller script (i.e. basic.py
        in this case). Use summary_key to set a default edit summary message.

    @type summary_key: str
    """

    summary_key = 'basic-changing'

    def __init__(self, generator, **kwargs) -> None:
        """
        Initializer.

        @param generator: the page generator that determines on which pages
            to work
        @type generator: generator
        """
        # Add your own options to the bot and set their defaults
        # -always option is predefined by BaseBot class
        self.available_options.update({
            'replace': False,  # delete old text and write the new text
            'summary': None,  # your own bot summary
            'text': 'Test',  # add this text from option. 'Test' is default
            'top': False,  # append text on top of the page
            'outpage': u'User:mastiBot/test',  # default output page
            'maxlines': 1000,  # default number of entries per page
            'test': False,  # print testoutput
            'progress': False,  # report progress
            'negative': False,  # if True negate behavior i.e. mark pages that DO NOT contain search string
        })

        # call initializer of the super class
        super().__init__(site=True, **kwargs)
        # assign the generator to the bot
        self.generator = generator

    def run(self):
        """TEST"""
        pywikibot.output(u'THIS IS A RUN METHOD')
        outputpage = self.getOption('outpage')
        pywikibot.output(u'OUTPUTPAGE:%s' % outputpage)

        # create structure for output
        arts = {}
        pagecounter = 0

        for p in self.generator:
            if self.getOption('test') or self.getOption('progress'):
                pywikibot.output(u'[%s] Treating #%i: %s' % (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pagecounter, p.title()))
                pagecounter += 1

            arts[p.title()] = self.treat(p)

        self.generateresultspage(arts, self.getOption('outpage'), '', '')

    def toMain(self, page):
        # return main namespace object
        #pywikibot.output("toMain NAMESPACE: %i" % page.namespace())
        if page.namespace() == 1:
            return (page.toggleTalkPage())
        else:
            return page

    def treat(self, page) -> None:
        """Load the given page, do some changes, and save it."""
        text = page.text

        ################################################################
        # NOTE: Here you can modify the text in whatever way you want. #
        ################################################################

        page = self.toMain(page)
        #pywikibot.output("NAMESPACE %i" % page.namespace())
        sex = self.checkWomen(page)
        pywikibot.output("PŁEĆ:%s" % sex)
        return(sex)

    def checkWomen(self, art):
        # check if the article is about woman
        # using WikiData
        try:
            d = art.data_item()

            dataItem = d.get()
            claims = dataItem['claims']
        except:
            return ("NO WIKIDATA")
        try:
            gender = claims["P21"]
        except:
            return ("NO GENDER")
        for c in gender:
            cjson = c.toJSON()
            genderclaim = cjson[u'mainsnak'][u'datavalue'][u'value'][u'numeric-id']
            if u'6581072' == str(genderclaim):
                if self.getOption('test'):
                    pywikibot.output(u'%s:Woman' % art.title())
                return ("woman")
            else:
                if self.getOption('test'):
                    pywikibot.output(u'%s:Man' % art.title())
                return ("other")
        return ("NO VALUE")

    def generateresultspage(self, redirlist, pagename, header, footer):
        """
        Generates results page from redirlist
        Starting with header, ending with footer
        Output page is pagename
        """
        finalpage = header
        # res = sorted(redirlist, key=redirlist.__getitem__, reverse=False)
        res = redirlist.keys()
        itemcount = 0

        for i in res:
            if redirlist[i] == 'woman':
                finalpage += '\n# [[%s]]' % i

        finalpage += footer

        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        outpage.text = finalpage

        if self.getOption('test'):
            pywikibot.output(outpage.title())

        outpage.save(summary=self.getOption('summary'))

def main(*args: Tuple[str, ...]) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    """
    options = {}
    # Process global arguments to determine desired site
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    gen_factory = pagegenerators.GeneratorFactory()

    # Parse command line arguments
    for arg in local_args:

        # Catch the pagegenerators options
        if gen_factory.handleArg(arg):
            continue  # nothing to do here

        # Now pick up your own options
        arg, sep, value = arg.partition(':')
        option = arg[1:]
        if option in ('summary', 'text'):
            if not value:
                pywikibot.input('Please enter a value for ' + arg)
            options[option] = value
        # take the remaining options as booleans.
        # You will get a hint if they aren't pre-defined in your bot class
        else:
            options[option] = True

    # The preloading option is responsible for downloading multiple
    # pages from the wiki simultaneously.
    gen = gen_factory.getCombinedGenerator(preload=True)
    if gen:
        # pass generator and private options to the bot
        bot = BasicBot(gen, **options)
        bot.run()  # guess what it does
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
