#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An incomplete sample script.

This is not a complete bot; rather, it is a template from which simple
bots can be made. You can rename it to mybot.py, then edit it in
whatever way you want.

Use global -simulate option for test purposes. No changes to live wiki
will be done.


The following parameters are supported:

-always           The bot won't ask for confirmation when putting a page

-text:            Use this text to be added; otherwise 'Test' is used

-replace:         Don't add text but replace it

-top              Place additional text on top of the page

-summary:         Set the action summary message for the edit.


The following generators and filters are supported:

&params;
"""
#
# (C) Pywikibot team, 2006-2020
#
# Distributed under the terms of the MIT license.
#
from typing import Tuple

import pywikibot
from pywikibot import pagegenerators, textlib, config2
import urllib, urllib.request
import datetime
from memento_client import MementoClient
import re

from pywikibot.bot import (
    SingleSiteBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)

try:
    import memento_client
    from memento_client.memento_client import MementoClientException
except ImportError as e:
    memento_client = e

import requests

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


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
            'outpage': u'User:mastiBot/sports-reference', #default output page
            'maxlines': 1000, #default number of entries per page
            'test': False, # print testoutput

        })

        # call initializer of the super class
        super().__init__(site=True, **kwargs)
        # assign the generator to the bot
        self.generator = generator


    def _get_closest_memento_url(self, url, when=None, timegate_uri=None):
        """Get most recent memento for url."""
        if isinstance(memento_client, ImportError):
            raise memento_client
    
        if not when:
            when = datetime.datetime.now()
    
        mc = memento_client.MementoClient()
        if timegate_uri:
            mc.timegate_uri = timegate_uri
    
        retry_count = 0
        while retry_count <= config2.max_retries:
            try:
                memento_info = mc.get_memento_info(url, when)
                break
            except (requests.ConnectionError, MementoClientException) as e:
                error = e
                retry_count += 1
                pywikibot.sleep(config2.retry_wait)
        else:
            raise error
    
        mementos = memento_info.get('mementos')
        if not mementos:
            raise Exception(
                'mementos not found for {0} via {1}'.format(url, timegate_uri))
        if 'closest' not in mementos:
            raise Exception(
                'closest memento not found for {0} via {1}'.format(
                    url, timegate_uri))
        if 'uri' not in mementos['closest']:
            raise Exception(
                'closest memento uri not found for {0} via {1}'.format(
                    url, timegate_uri))
        return mementos['closest']['uri'][0]

    def get_archive_url(self, url):
        """Get archive URL."""
        try:
            archive = self._get_closest_memento_url(
                url,
                timegate_uri='http://web.archive.org/web/')
        except Exception:
            archive = self._get_closest_memento_url(
                url,
                timegate_uri='http://timetravel.mementoweb.org/webcite/timegate/')
    
        # FIXME: Hack for T167463: Use https instead of http for archive.org links
        if archive.startswith('http://web.archive.org'):
            archive = archive.replace('http://', 'https://', 1)
        return archive

    def treat(self,page) -> None:
        """Load the given page, do some changes, and save it."""
        text = page.text
        line = [] 
 
        #linkR = re.compile(r'(?P<url>http[s]?://[^\]\s<>\"]*?[^\]\s\.:;,<>\"\|\)](?=[\]\s\.:;,<>\"\|\)]*\'\')|http[s]?://[^\]\s<>\"]*[^\]\s\.:;,<>\"\|\)])')
        linkR = re.compile(r'(?m)(?P<url>http[s]?:(\/\/[^\s\?]+?)(\??[^\s<\|\}\]]*))(?:[\]\s\.<\|\}])')
        #linkR = textlib.compileLinkR()
        for m in linkR.finditer(text):
            if m.group('url'):
                url = m.group('url')
                #pywikibot.output('URL:{0}'.format(url))
            else:
                pywikibot.output('wrong link')
                continue

            if url.startswith(('http://sports-reference.com/olympics','http://www.sports-reference.com/olympics')):
                result = {
                    'url' : None,
                    'memento' : None,
                }
                result['url'] = url
                pywikibot.output('PROCESSING URL:{0}'.format(url))
                try:
                    result['memento'] = self.get_archive_url(url)
                except KeyboardInterrupt:
                    pass

                pywikibot.output('URL        :%s' % result['url'])
                #pywikibot.output('ARCHIVE.ORG:%s' % result['arch'])
                #pywikibot.output('MEMENTO    :%s' % result['memento'])
                #pywikibot.output('MEMENTO DIR:%s' % result['client'])
                line.append(result)

        print(line)
        return(line)

    def generateresultspage(self, redirlist, pagename, header, footer):
        """
        Generates results page from redirlist
        Starting with header, ending with footer
        Output page is pagename
        """
        maxlines = int(self.getOption('maxlines'))
        finalpage = header
        if self.getOption('test'):
            pywikibot.output(u'GENERATING RESULTS')
        for p in redirlist.keys():
            if self.getOption('test'):
                pywikibot.output('RESULTS FOR:%s' % p)
            subrows = len(redirlist[p])
            finalpage += '\n|-\n| '
            if subrows > 1: #multirow result
                finalpage += 'rowspan="%i" | [[%s]] || ' % (subrows, p)
                first = True
                for r in redirlist[p]:
                    if not first:
                        finalpage += '\n|-\n| '
                    else:
                        first = False
                    finalpage += '%s || %s || %s || %s' % (r['url'], r['memento'])
            else:
                for r in redirlist[p]:
                    finalpage += '[[%s]] || %s || %s || %s || %s' % (p, r['url'], r['memento'])

        finalpage += footer
        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        outpage.text = finalpage
        if self.getOption('test'):
            pywikibot.output(outpage.title())
            pywikibot.output(outpage.text)
        
        outpage.save(summary=self.getOption('summary'))
        return(True)

    def run(self):
        header = u"Ta strona jest okresowo uaktualniana przez [[Wikipedysta:MastiBot|MastiBota]]. Ostatnia aktualizacja ~~~~~. \n"
        header += u"Wszelkie uwagi proszę zgłaszać w [[Dyskusja_Wikipedysty:Masti|dyskusji operatora]].\n\n"
        header += '{| class="wikitable"\n'
        header += '! strona !! link !! archive\n'

        reflinks = {} #initiate list
        counter = 0
        marked = 0
        for tpage in self.generator:
            counter += 1
            if self.getOption('test'):
                pywikibot.output(u'Treating #%i (%i marked): %s' % (counter, marked, tpage.title()))
            refs = self.treat(tpage) # get (name)
            #if self.getOption('test'):
                #pywikibot.output(u'%s' % refs)
            if refs:
                reflinks[tpage.title()] = refs
                marked += 1

        footer = u'\n|}\n\nPrzetworzono ' + str(counter) + u' stron'

        outputpage = self.getOption('outpage')

        result = self.generateresultspage(reflinks,outputpage,header,footer)


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
