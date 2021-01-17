#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An incomplete sample script by masti for creating statistics/listings pages

Usage:
python pwb.py masti/m-isap.py -page:"Wikipedysta:MastiBot/DU" -summary:"Bot poprawia odwołania do ustawy" -outpage:'Wikipedysta:MastiBot/DU/log' -pt:0
Page should contain a list of {{Dziennik Ustaw}} linking to a new wersion of law.

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
from bs4 import BeautifulSoup
import urllib2
import difflib

__version__ = '$Id: c1795dd2fb2de670c0b4bddb289ea9d13b1e9b3f $'
#

import pywikibot
from pywikibot import pagegenerators
import re
from datetime import datetime

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
    WUs = {}  # dict to keep info on processed templates

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
            'outpage': u'User:mastiBot/test',  # default output page
            'maxlines': 10000,  # default number of entries per page
            'test': False,  # print testoutput
            'negative': False,  # if True negate behavior i.e. mark pages that DO NOT contain search string
            'id': '20190000506',  # starting isap page id - for test only
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

        footer = u'\n|}\n'

        finalpage = self.prepareheader()
        licznik = 0
        wiersz = 0
        #pagelist = [page for page in self.generator]
	#pagelist.sort()
        #for page in pagelist:
	for page in self.generator:
            licznik += 1
            #finalpage = finalpage + self.treat(page)
            pywikibot.output(u'Processing page #%s (%s marked): %s' % (str(licznik), str(wiersz), page.title(asLink=True)) )
            result = self.treat(page)
            if not result == u'':
               wiersz += 1
               finalpage += u'\n|-\n| ' + str(wiersz) + u' || ' + result
               pywikibot.output(u'Added line #%i: %s' % ( wiersz, u'\n|-\n| ' + str(wiersz) + u' || ' + result))
            #pywikibot.output(finalpage)
        finalpage += footer
	finalpage += u'\nPrzetworzono stron: ' + str(licznik)

	finalpage = self.przypisy(finalpage)

        #Save page
        #pywikibot.output(finalpage)
        outputpage = self.getOption('outpage')
        pywikibot.output(u'OUTPUTPAGE:%s' % outputpage)

        outpage = pywikibot.Page(pywikibot.getSite(), self.outputpage)
        if not self.save(finalpage, outpage, self.summary):
           pywikibot.output(u'Page %s not saved.' % outpage.title(asLink=True))

    def prepareheader(self):
        #prepare new page with table
        header = u"Ta strona jest okresowo uaktualniana przez [[Wikipedysta:MastiBot|bota]]. Ostatnia aktualizacja ~~~~~. \nWszelkie uwagi proszę zgłaszać w [[Dyskusja_Wikipedysty:Masti|dyskusji operatora]]."
	header += u"\n\nStrona zawiera artykuły, w których wykryto niezgodność nazwisk lub lat urodzenia/śmierci."
	header += u"\n<small>"
	header += u"\n*Legenda:"
	header += u"\n*:'''Hasło''' - Tytuł hasła"
        header += u"\n*:'''Nagłówek''' - Nazwa wyróżniona"
	header += u"\n*:'''Data urodzenia''' - Data urodzenia w nagłówku"
	header += u"\n*:'''Data śmierci''' - Data śmierci w nagłówku"
	header += u"\n*:'''Kategoria Urodzeni w''' - Rok w kategorii urodzonych"
	header += u"\n*:'''Kategoria zmarli w''' - Rok w kategorii zmarłych"
	header += u"\n*:'''Infoboksy''' - liczba infoboksów"
	header += u"\n*:'''Infobox''' - tytuł infoboksu"
	header += u"\n*:'''Nazwisko w infoboksie'''"
	header += u"\n*:'''Data urodzenia w infoboksie'''"
	header += u"\n*:'''Data śmierci w infoboksie'''"
	header += u"\n</small>\n"
	header += u'{| class="wikitable" style="font-size:85%;"\n|-\n!Lp.\n!Hasło\n!Nagłówek\n!Data urodzenia\n!Data śmierci\n'
	header += u'!Kategoria<br />Urodzeni w\n!Kategoria<br />zmarli w\n!Infoboksy\n!Infobox\n!Nazwisko<br />w infoboksie\n!Data urodzenia<br />w infoboksie\n!Data śmierci<br />w infoboksie'
        return(header)
      
    def przypisy(self, text):
	"""
	Searches text for references, adds {{Przypisy}} if found.
	"""
	#przypisy?
	refR = re.compile(ur'(?P<ref>(<ref|\{\{r))',flags=re.I)
	refs = refR.finditer(text) #ptitleR.search(pagetitle).group('ptitle')
	reffound = False
	for ref in refs:
	   reffound = True
	   break
	if reffound:
	   text += u'\n\n{{Przypisy}}'
        return(text)

    def refremove(self, intext):
        """
        remove references from text
        """
        refR = re.compile(ur'(<ref.*?<\/ref>|\{\{r\|.*?\}\}|\{\{u\|.*?\}\})')
        output = re.sub(refR, u'', intext)
        #pywikibot.output(output)
        return(output)


    def treat(self, page):
        """
        Loads the given page, looks for interwikis
        """
        found = False
        rowtext = u''
        textload = page.text
        if not textload:
            return(u'')
        
        text = self.refremove(textload)
        #pywikibot.output(text)
	#First paragraph
	firstparR = re.compile(ur"(^|\n)(?P<firstpar>'''.*\n)")
        firstpars = u''
        firstline = True
        linki = firstparR.finditer(text)
        for firstpar in linki:
           found = True
           pywikibot.output(u'Firstpar: %s' % firstpar.group('firstpar'))
           break
	if found:
	   firstpars = firstpar.group('firstpar')

	#page title no disambig
	ptitleR = re.compile(ur'(?P<ptitle>.*?) \(')
	pagetitle = page.title()
	if u'(' in pagetitle:
	    ptitle = ptitleR.search(pagetitle).group('ptitle')
	else:
	    ptitle = pagetitle
	pywikibot.output(u'PTitle (no disambig): %s' % ptitle)
        
        #bolded header
        bheaderR = re.compile(ur"(^|\n)'''(?P<header>.*?)'''",flags=re.I)
        bheaders = u''
        firstline = True
        linki = bheaderR.finditer(firstpars)
        for bheader in linki:
           found = True
           pywikibot.output(u'Header: %s' % bheader.group('header'))
           if firstline:
              firstline = False
              bheaders += bheader.group('header')
           else:
              bheaders += u'<br />' + bheader.group('header')
           break

        #bolded birthday  ur\.\s*(\[\[)?\d*\s*\w*(\]\])?\s*(\[\[)?\d*
        bbdayR = re.compile(ur"ur\.(\s*w)?(\s*(\[{2})?(?P<bbd>\d{1,2} [\wśńź]{4,12})(\]{2})?)?\s*?(\[{2})?(?P<bby>\d{4})(\]{2})?",flags=re.I)
        bbd = u''
	bby = u''
        firstline = True
        linki = bbdayR.finditer(firstpars)
        for bday in linki:
           found = True
           pywikibot.output(u'BDAY: %s %s' % (bday.group('bbd'),bday.group('bby')))
	   if not bday.group('bbd') == None:
	      bbd = bday.group('bbd')
	   if not bday.group('bby') == None:
	      bby = bday.group('bby')
           pywikibot.output(u'BDAY set: %s %s' % (bbd, bby))
           break

	#bolded death
        bddayR = re.compile(ur"zm\.(\s*w)?(\s*(\[{2})?(?P<bdd>\d{1,2} [\wśńź]{4,12})(\]{2})?)?\s*?(\[{2})?(?P<bdy>\d{4})(\]{2})?",flags=re.I)
        bdd = u''
	bdy = u''
        firstline = True
        linki = bddayR.finditer(firstpars)
        for dday in linki:
           found = True
           pywikibot.output(u'DDAY: %s %s' % (dday.group('bdd'),dday.group('bdy')))
	   if not dday.group('bdd') == None:
	      bdd = dday.group('bdd')
	   if not dday.group('bdy') == None:
	      bdy = dday.group('bdy')
           pywikibot.output(u'DDAY set: %s %s' % (bdd, bdy))
           break

        #Category birthyear
        cbyearR = re.compile(ur"\[\[Kategoria:Urodzeni w (?P<cby>.*?)[\|\]]")
	cby = u''
        firstline = True
        linki = cbyearR.finditer(text)
        for cbyear in linki:
           found = True
           #pywikibot.output(u'CATBYEAR: %s' % cbyear.group('cby'))
	   cby = cbyear.group('cby')
           pywikibot.output(u'CATBYEAR: %s' % cby)
           break

        #Category deathyear
        cdyearR = re.compile(ur"\[\[Kategoria:Zmarli w (?P<cdy>.*?)[\|\]]")
	cdy = u''
        firstline = True
        linki = cdyearR.finditer(text)
        for cdyear in linki:
           found = True
           #pywikibot.output(u'CATDYEAR: %s' % cdyear.group('cdy'))
	   cdy = cdyear.group('cdy')
           pywikibot.output(u'CATDYEAR: %s' % cdy)
           break

	#infobox name & title
	firstline = True
	infoboxs = u''
        iboxname = u''
        iboxbd = u''
        iboxby = u''
        iboxdd = u''
        iboxdy = u''
        infoboxtitle = u''
	infoboxtR = re.compile(ur"\{\{(?P<iboxtitle>.*) infobox",flags=re.I)
	infoboxnR = re.compile(ur"^(Imię i nazwisko|Imię|polityk|imięinazwisko|imię i nazwisko|imięnazwisko)\s*=\s*(?P<iboxname>.*)",flags=re.I)
	infoboxbdR = re.compile(ur"^(data urodzenia|dataurodzenia|data i miejsce urodzenia)\s*=(\s*(\[{2})?(?P<iboxbd>\d{1,2} [\wśńź]{4,12})(\]{2})?)?\s*?(\[{2})?(?P<iboxby>\d{4})(\]{2})?",flags=re.I)
	infoboxddR = re.compile(ur"^(data śmierci|dataśmierci|data i miejsce śmierci)\s*=(\s*(\[{2})?(?P<iboxdd>\d{1,2} [\wśńź]{4,12})(\]{2})?)?\s*?(\[{2})?(?P<iboxdy>\d{4})(\]{2})?",flags=re.I)
	infoboxnumber = 0
	infoboxskip = False
        for (t, args) in page.templatesWithParams():
	   if u'infobox' in t and not u'/' in t:
	      iboxname = u''
	      iboxbd = u''
	      iboxby = u''
	      iboxdd = u''
	      iboxdy = u''
	      infoboxnumber += 1
	      if infoboxskip:
	         break
	      for p in args:
                 p = self.refremove(p)
	         pywikibot.output(p)
	         #name in infobox
                 arglist = infoboxnR.finditer(p)
	         for arg in arglist:
	            pywikibot.output(u'ARG: %s' % arg.group('iboxname'))
	            iboxname = arg.group('iboxname')
	         #birthdate and year in infobox
                 arglist = infoboxbdR.finditer(p)
	         for arg in arglist:
	            pywikibot.output(u'ARG: %s %s' % (arg.group('iboxbd'),arg.group('iboxby')))
	            if not arg.group('iboxbd') == None:
	               iboxbd = arg.group('iboxbd')
	            if not arg.group('iboxby') == None:
	               iboxby = arg.group('iboxby')
	         #deathdate and year in infobox
                 arglist = infoboxddR.finditer(p)
	         for arg in arglist:
	            pywikibot.output(u'ARG: %s %s' % (arg.group('iboxdd'),arg.group('iboxdy')))
	            if not arg.group('iboxdd') == None:
	               iboxdd = arg.group('iboxdd')
	            if not arg.group('iboxdy') == None:
	               iboxdy = arg.group('iboxdy')
	      pywikibot.output(u'iboxname: %s' % iboxname)
	      pywikibot.output(u'iboxbd: %s' % iboxbd)
	      pywikibot.output(u'iboxby: %s' % iboxby)
	      pywikibot.output(u'iboxdd: %s' % iboxdd)
	      pywikibot.output(u'iboxdy: %s' % iboxdy)

	      #if firstline:
              #   firstline = False
              #else:
              #   infoboxs += u'<br />'
              #infoboxs += t + u'=>' + iboxname + u'=>' + iboxbd + u' ' + iboxby + u'=>' + iboxdd + u' ' + iboxdy
	      infoboxs += t + u' || ' + iboxname + u' || ' + iboxbd + u' ' + iboxby + u' || ' + iboxdd + u' ' + iboxdy
              infoboxtitle = t
	      infoboxskip = True

	#write result
	ToBeMarked = False
	pywikibot.output(u'ptitle: %s' % ptitle)
	pywikibot.output(u'bheaders: %s' % bheaders)
	pywikibot.output(u'infoboxskip: %s' % infoboxskip)
	if not iboxname == ptitle or not iboxname == bheaders:
	   cond1 = True
	else:
	   cond1 = False
	pywikibot.output(u'Condition1: %s' % cond1)
	pywikibot.output(u'Condition2: %s' % (infoboxskip and cond1))
	if not ptitle == bheaders or (infoboxskip and (not iboxname == ptitle or not iboxname == bheaders)) :
	   ToBeMarked = True
	   pywikibot.output(u'ToBeMarked: title vs bolded header')
           ptitle = u'style="background-color:PowderBlue" | ' + ptitle
           bheaders = u'style="background-color:PowderBlue" | ' + bheaders
           iboxname = u'style="background-color:PowderBlue" | ' + iboxname
	if not bby == cby or (infoboxskip and (not iboxby == bby or not iboxby == cby)):
	   ToBeMarked = True
	   pywikibot.output(u'ToBeMarked: Bolded BY vs cat BY')
           bby = u'style="background-color:Lime" | ' + bby
           cby = u'style="background-color:Lime" | ' + cby
           iboxbd = u'style="background-color:Lime" | ' + iboxbd
	if not bdy == cdy or (infoboxskip and (not iboxdy == bdy or not iboxdy == cdy)):
	   ToBeMarked = True
	   pywikibot.output(u'ToBeMarked: Bolded DY vs cat DY')
           bdy = u'style="background-color:Orange" | ' + bdy
           cdy = u'style="background-color:Orange" | ' + cdy
           iboxdd = u'style="background-color:Orange" | ' + iboxdd
	if ToBeMarked:
           pageiw = u'[[:' + page.title() + u']] || ' + bheaders + u' || ' + bbd + u' ' + bby + u' || ' + bdd + u' ' + bdy + u' || ' + cby + u' || ' + cdy + u' || ' + str(infoboxnumber) + u' || ' + infoboxtitle + u' || ' + iboxname + u' || ' + iboxbd + u' ' + iboxby + u' || ' + iboxdd + u' ' + iboxdy
	else:
	   pageiw = u''

        #test print
        pywikibot.output(u"%s" % pageiw)

	return(pageiw)


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
        if option in ('summary', 'text', 'outpage', 'maxlines', 'id'):
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
