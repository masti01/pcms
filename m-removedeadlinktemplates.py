#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This is a bot to remove {{Martwy link dyskusja}} templates from discussion pages if the link reported no longer exists in the article.
Call:
   python pwb.py masti/m-removedeadlinktemplates.py -catr:"Kategoria:Niezweryfikowane martwe linki" -ns:1 -summary:"Bot usuwa zbędne szablony martwego linku" -pt:0

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
            'test': False, #switch on test functionality
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
        for page in self.generator:
            self.treat(page)

    def treat(self, page):
        """
        Loads the given discussion page, verifies if the links in {{Martwy link dyskusja}}
        were removed from article or are a part of {{Cytuj}} template with properly filled archiwum= parameter
        Then removes the template(s) or marks page for deletion
        """
        
	disctext = page.text
        if not disctext:
            return
        articlepage = page.toggleTalkPage()
        articletext = articlepage.text
        if not articletext:
            return

        #test printout
        if self.getOption('test'):
                pywikibot.output(u'Page: %s' % articlepage.title(asLink=True))
        pywikibot.output(u'Discussion: %s' % page.title(asLink=True))

        #find dead link templates
        #linkR = re.compile(ur'\{\{(?P<infobox>([^\]\n\|}]+?infobox))')
        tempR = re.compile(ur'(?P<template>\{\{Martwy link dyskusja[^}]*?}}\n*?)')
        weblinkR = re.compile(ur'link\s*?=\s*?\*?\s*?(?P<weblink>[^\n\(]*)')
        links = u''
        changed = False
        templs = tempR.finditer(disctext)
        for link in templs:
            template = link.group('template').strip()
	    #pywikibot.output(template)
            weblink = re.search(weblinkR,template).group('weblink').strip()
            if weblink in articletext:
                if self.getOption('test'):
                    pywikibot.output(u'Still there >>%s<<' % weblink)
                if not self.removelinktemplate(weblink,articletext):
                    if self.getOption('test'):
                        pywikibot.output(u'Should stay >>%s<<' % weblink )
                else:
                    pywikibot.output(u'Has to go >>%s<<' % weblink )
                    disctext = re.sub(re.escape(template), u'', disctext)
                    changed = True
            else:
                if self.getOption('test'):
                    pywikibot.output(u'Uuups! 404 - link not found >>%s<<' % weblink)
                disctext = re.sub(re.escape(template), u'', disctext)
                changed = True
 
        if changed:
            if len(disctext) < 4:
                #pywikibot.output(u'Deleting {0}.'.format(page))
                #disctext = u'{{ek|Pusta strona dyskusji - usunięte szablony martwych linków}}\n\n' + disctext
                if self.getOption('test'):
                    page.delete(reason=self.getOption('summary'), prompt=True, mark=True, quit=True)
                else:
                    page.delete(reason=self.getOption('summary'), prompt=False)
            else:
                #pywikibot.output(u'Removing template from {0}'.format(page))
                page.text = disctext
                page.save(summary=self.getOption('summary'))

    def removelinktemplate(self,link, text):
        """
        check if link is within {{cytuj...}} template with filled archiwum= field or within this field
	conditions on link removal:
	    link in url/tytuł field + archiwum not empty
	    link in archiwum field
        """
        citetempR = re.compile(ur'(?P<citetemplate>\{\{[cC]ytuj.*?\|[^}]*?\}\})')
        urlfieldR = re.compile(ur'(url|tytuł)\s*?=(?P<url>[^\|\}]*)')
        archfieldR = re.compile(ur'archiwum\s*?=\s*?(?P<arch>[^\|\}]*)')
        result = False
        
        cites = citetempR.finditer(text)
        for c in cites:
            citetemplate = c.group('citetemplate').strip()
            if self.getOption('test'):
                pywikibot.output(u'Cite:%s' % citetemplate)
            try:
                urlfield = re.search(urlfieldR,citetemplate).group('url').strip()
            except AttributeError:
                pywikibot.output(u'No URL field')
                continue
            #pywikibot.output(u'URL:%s' % urlfield) 
            try:
                archfield = re.search(archfieldR,citetemplate).group('arch').strip()
            except AttributeError:
                if self.getOption('test'):
                    pywikibot.output(u'No ARCH field')
                continue
            if self.getOption('test'):
                pywikibot.output(u'URL2:%s' % urlfield)            
                pywikibot.output(u'Arch2:%s' % archfield)
            if link in urlfield:
                if self.getOption('test'):
                    pywikibot.output(u'URL in URL field')            
                if (len(archfield) > 0):
                    if self.getOption('test'):
                        pywikibot.output(u'ARCHIVE field filled in')
                    result = True
            else:
                if self.getOption('test'):
                    pywikibot.output(u'URL not found in template')

        return(result)

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
        if option in ('summary', 'text'):
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
