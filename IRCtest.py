#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
A script that displays the ordinal number of the new articles being created
visible on the Recent Changes list. The script doesn't make any edits, no bot
account needed.

Note: the script requires the Python IRC library
http://python-irclib.sourceforge.net/
"""

# Author: Balasyum
# http://hu.wikipedia.org/wiki/User:Balasyum
# License : LGPL
__version__ = '$Id: 229b3e02cf110f5e9d7f8d16c60906ee9769b7af $'

import re

import pywikibot
import externals
externals.check_setup('irclib')
from ircbot import SingleServerIRCBot


class ArtNoDisp(SingleServerIRCBot):

    def __init__(self, site, channel, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.site = site
        ns = []
        for n in site.namespaces():
            if isinstance(n, tuple):  # I am wondering that this may occur!
                ns += n[0]
            else:
                ns += [n]
        self.other_ns = re.compile(
            u'14\[\[07(' + u'|'.join(ns) + u')')
        self.api_url = self.site.api_address()
        self.api_url += 'action=query&meta=siteinfo&siprop=statistics&format=xml'
        self.api_found = re.compile(r'articles="(.*?)"')
        self.re_edit = re.compile(
            r'^C14\[\[^C07(?P<page>.+?)^C14\]\]^C4 (?P<flags>.*?)^C10 ^C02(?P<url>.+?)^C ^C5\*^C ^C03(?P<user>.+?)^C ^C5\*^C \(?^B?(?P<bytes>[+-]?\d+?)^B?\) ^C10(?P<summary>.*)^C'.replace(
                '^B', '\002').replace('^C', '\003').replace('^U', '\037'))

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        pass

    def on_pubmsg(self, c, e):
        #pywikibot.output(c)
        #pywikibot.output(e)
        source = unicode(e.source().split ( '!' ) [ 0 ], 'utf-8')
        text = unicode(e.arguments() [ 0 ], 'utf-8')
        #pywikibot.output(u'CONNECTION:%s' % unicode(c[ 0 ], 'utf-8'))
        pywikibot.output(u'SOURCE:%s' % source)
        pywikibot.output(u'TEXT:%s' % text)
        
        
        match = self.re_edit.match(e.arguments()[0])
        if not match:
                return
        #if not ('N' in match.group('flags')):
        #        return
        #try:
        #    msg = unicode(e.arguments()[0], 'utf-8')
        #except UnicodeDecodeError:
        #    return
        #pywikibot.output(u'MSG:%s'% msg)
        mpage = unicode(match.group('page'), 'utf-8')        
        mflags = unicode(match.group('flags'), 'utf-8')
        murl = unicode(match.group('url'), 'utf-8')    
        muser = unicode(match.group('user'), 'utf-8')
        mbytes = unicode(match.group('bytes'), 'utf-8')
        msummary = unicode(match.group('summary'), 'utf-8')
        pywikibot.output(u'PAGE:%s' % mpage)
        pywikibot.output(u'FLAGS:%s' % mflags)
        pywikibot.output(u'URL:%s' % murl)
        pywikibot.output(u'USER:%s' % muser)
        pywikibot.output(u'BYTES:%s' % mbytes)
        pywikibot.output(u'SUMMARY:%s' % msummary)
     

        '''
        if self.other_ns.match(msg):
            return
        name = msg[8:msg.find(u'14', 9)]
        text = self.site.getUrl(self.api_url)
        entry = self.api_found.findall(text)
        
        page = pywikibot.Page(self.site, name)
        try:
                text = page.get()
        except pywikibot.NoPage:
                return
        except pywikibot.IsRedirectPage:
                return
        print entry[0], name
        '''

    def on_dccmsg(self, c, e):
        pass

    def on_dccchat(self, c, e):
        pass

    def do_command(self, e, cmd):
        pass

    def on_quit(self, e, cmd):
        pass


def main():
    site = pywikibot.getSite()
    site.forceLogin()
    chan = '#' + site.language() + '.' + site.family.name
    #bot = ArtNoDisp(site, chan, site.loggedInAs(), "irc.wikimedia.org")
    bot = ArtNoDisp(site, chan, 'mastiBotIRC', "irc.wikimedia.org")
    bot.start()

if __name__ == "__main__":
    main()
