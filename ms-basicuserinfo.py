#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An incomplete sample script by masti for creating statistics/listings pages: user activity
Usage:
python pwb.py masti/ms-basicuserinfo.py -links:'Wikipedia:Atlas wikipedystów/województwo dolnośląskie' -ns:user -summary:"Bot uaktualnia stronę" -pt:0 -outpage:'Wikipedysta:mastiBot/Aktywni/Wrocław'

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
import datetime
from pywikibot import Timestamp

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
            'test': False, # print testoutput
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
        """TEST"""
        header = "Ostatnia aktualizacja przez bota: '''~~~~~'''.\n\n"
        footer = '\n\n'

        result = []

        pywikibot.output(u'THIS IS A RUN METHOD')
        outputpage = self.getOption('outpage')
        pywikibot.output(u'OUTPUTPAGE:%s' % outputpage)
        for p in self.generator:
            pywikibot.output(u'Treating: %s' % p.title())
            #user = pywikibot.User(p)
            result.append(self.treat(pywikibot.User(p)))
            """
            props = user.getprops()
            print props
            for p in props.keys():
                pywikibot.output(u'%s:%s' % (p,props[p]))
            pywikibot.output("user:%s" % user.username)
            pywikibot.output("register:%s" % user.registration())
            pywikibot.output("edits:%i" % user.editCount())
            pywikibot.output("blocked:%s" % user.isBlocked())
            if user.last_edit:
                pywikibot.output("lastEdit:%s revid:%s ts:%s comm:%s" % user.last_edit)  #Page, revid, pywikibot.Timestamp, comment
            else:
                pywikibot.output("lastEdit: NONE")
            """
        print(result)

        self.saveArticleList(result,self.getOption('outpage'),header,'')

    def treat(self,user):

        res = {}
        res['user'] = user.username
        res['regDate'] = user.registration()
        res['editCount'] = user.editCount()
        res['blocked'] = user.isBlocked()
        if user.last_edit:
            le = {}
            p,r,t,c = user.last_edit
            le['page'] = p.title()
            le['revid'] = r
            le['time'] = str(t)
            le['comment'] = c
        else:
            le = None
        res['lastEdit'] = le
        # count contributions in last month, 3m & 12m
        res['edit30d'] = 0
        res['edit90d'] = 0
        res['edit360d'] = 0
        currTime = Timestamp.utcnow()
	curTime30d = currTime - datetime.timedelta(days=30)
	curTime90d = currTime - datetime.timedelta(days=90)
	curTime360d = currTime - datetime.timedelta(days=360)
        for rp,rid,rt,rc in user.contributions(total=0):
            if rt > curTime30d:
                res['edit30d'] += 1
            if rt > curTime90d:
                res['edit90d'] += 1
            if rt > curTime360d:
                res['edit360d'] += 1
            else:
                break
        """
        pywikibot.output("user:%s" % user.username)
        pywikibot.output("register:%s" % user.registration())
        pywikibot.output("edits:%i" % user.editCount())
        pywikibot.output("blocked:%s" % user.isBlocked())
        if user.last_edit:
            pywikibot.output("lastEdit:%s revid:%s ts:%s comm:%s" % user.last_edit)  #Page, revid, pywikibot.Timestamp, comment
        else:
            pywikibot.output("lastEdit: NONE")
        """
        pywikibot.output(res)
        return(res)

    def saveArticleList(self, res, pagename, header, footer):
        # save article list at self.getOption('outpage')/list
        # generate table header

        finalpage = header
        finalpage += u'\n{| class="wikitable sortable" style="text-align: center;"'
        finalpage += u'\n|-'
        finalpage += u'\n! #'
        finalpage += u'\n! Użytkownik'
        finalpage += u'\n! Ostatnia edycja'
        finalpage += u'\n! Strona'
        finalpage += u'\n! Liczba edycji<br />ogółem'
        finalpage += u'\n! Liczba edycji<br />30 dni'
        finalpage += u'\n! Liczba edycji<br />90 dni'
        finalpage += u'\n! Liczba edycji<br />360 dni'
        finalpage += u'\n! Zablokowany'

        count = 0
        for a in res:
            count += 1
            if a['lastEdit']:
                t = a['lastEdit']['time']
                p = '[[:%s]]' % a['lastEdit']['page']
            else:
                t = ''
                p = ''
            if a['blocked']:
                b = '{{Tak}}'
            else:
                b = ''
            finalpage += u'\n|-\n|'
            finalpage += u'%i. || [[Wikipedysta:%s|%s]] || %s || %s || %i || %i || %i || %i || %s' % (count, a['user'], a['user'], t, p, a['editCount'], a['edit30d'], ['edit360d'], ['edit360d'], b)

        finalpage += u'\n|}'
        finalpage += footer

        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if self.getOption('test'):
            pywikibot.output(u'ArticleList:%s' % outpage.title())
        outpage.text = finalpage
        outpage.save(summary=self.getOption('summary'))

        return




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
