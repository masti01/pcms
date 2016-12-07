#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This is a bot to remove template {{Przypisy}} if no reference in article present
Call:
   python pwb.py masti/m-reftemplate.py -transcludes:Przypisy -outpage:"Wikipedysta:mastiBot/refTemplate" -maxlines:100 -summary:"Bot usuwa zbędny szablon {{s|Przypisy}}"

Use global -simulate option for test purposes. No changes to live wiki
will be done.

The following parameters are supported:

&params;

-always           If used, the bot won't ask if it should file the message
                  onto user talk page.

-text:            Use this text to be added; otherwise 'Test' is used

-replace:         Dont add text but replace it

-top              Place additional text on top of the page

-summary:         Set the action summary message for the edit.

-outpage          Results page; otherwise "Wikipedysta:mastiBot/test" is used

-maxlines         Max number of entries before new subpage is created; default 1000

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

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}
refTemplates = [ 
    u'Okres geologiczny infobox'
    u'Zwierzę infobox'
    u'Hetmani wielcy litewscy'
    u'Przesilenia'
    u'Równonoce'
    u'Wartość odżywcza'
    u'Ziemia-Śnieżka'
    u'Związki cywilne osób tej samej płci'
    u'Rynek alternatywnych przeglądarek internetowych'
    u'Linia czasu modeli iPhone'
    u'Ostatnie stabilne wydanie/Gnome'
    u'Ostatnie stabilne wydanie/KDE'
    u'Ostatnie testowe wydanie/KDE'
    u'Ostatnie stabilne wydanie/Konqueror'
    u'Ostatnie stabilne wydanie/mIRC'
]

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
            'test': False, #switch on test functionality
            'outpage': u'User:mastiBot/test', #default output page
            'maxlines': 1000, #default number of entries per page
            'negative': False, #if True negate behavior i.e. mark pages that DO NOT contain search string
            'restart': False, #if restarting do not clean summary page       
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
        counter = 1
        onPageCount = 0
        marked = 0
        try:
            if self.getOption('restart'):
                self.saveProgress(self.getOption('outpage'), counter, marked, '', init=False, restart=True)
            else:
                self.saveProgress(self.getOption('outpage'), counter, marked, '', init=True, restart=False)
            for page in self.generator:
                pywikibot.output(u'Processing #%i (%i marked):%s' % (counter, marked, page.title(asLink=True)))
                counter += 1
                onPageCount += 1
                if onPageCount >= int(self.getOption('maxlines')):
                    self.saveProgress(self.getOption('outpage'), counter, marked, page.title(asLink=True))
                    onPageCount = 0
                if self.treat(page):
                    marked += 1
        finally:
            self.saveProgress(self.getOption('outpage'), counter, marked, page.title(asLink=True))
            pywikibot.output(u'Processed: %i, Orphans:%i' % (counter,marked))

    def treat(self, page):
        """Load the given page, do some changes, and save it."""
        text = page.text
        found = False

        for t in refTemplates:
            if t in text:
                found = True
        if found:     
            text = re.sub(ur'\n\{\{Przypisy.*?\}\}', u'', text, flags=re.IGNORECASE)
            
            if self.getOption('test'):
                pywikibot.input('Waiting...')
            # if summary option is None, it takes the default i18n summary from
            # i18n subdirectory with summary_key as summary key.
            self.save(text, summary=self.getOption('summary'))
        return(found)
         
    def saveProgress(self, pagename, counter, marked, lastPage, init=False, restart=False):
        """
        log run progress
        """
        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if init:
            outpage.text = u'Process started: ~~~~~'
        elif restart:
            outpage.text += u'\n:#Process restarted: ~~~~~'
        else:
            outpage.text += u'\n#' +str(counter) + u'#' + str(marked) + u' – ' + lastPage + u' – ~~~~~'
        outpage.save(summary=self.getOption('summary'))
        return

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
