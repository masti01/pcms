#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This bot creates a table of biografies with inconsistent parameters
Call: python m-biografiedaty.py -catr:Biografie -outpage:"Wikipedysta:MastiBot/problemy w biogramach" -summary:"Bot uaktualnia stronę"

The following parameters are supported:

&params;

-summary:XYZ      Set the summary message text for the edit to XYZ, bypassing
                  the predefined message texts with original and replacements
                  inserted.

All other parameters will be regarded as part of the title of a single page,
and the bot will only work on that single page.
"""
#
# (C) Pywikipedia bot team, 2006-2011
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: basic.py 10358 2012-06-13 12:29:02Z drtrigon $'
#

import re

import wikipedia as pywikibot
import pagegenerators
import re
import httplib, socket, urllib, urllib2, cookielib
from pywikibot import i18n

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

class BasicBot:
    # Edit summary message that should be used is placed on /i18n subdirectory.
    # The file containing these messages should have the same name as the caller
    # script (i.e. basic.py in this case)

    def __init__(self, generator, summary, outputpage, maxlines):
        """
        Constructor. Parameters:
            @param generator: The page generator that determines on which pages
                              to work.
            @type generator: generator.
            @param summary: Set the summary message text for the edit.
            @type summary: (unicode) string.
            @param outputpage: title of the output page
            @type outputpage: (unicode) string
            @param maxlines: maximum number of lines in output table
            @type maxlines: integer
        """
        self.generator = generator
        # init constants
        self.site = pywikibot.getSite(code=pywikibot.default_code)
        # Set the edit summary message
        if summary:
            self.summary = summary
        else:
            self.summary = i18n.twtranslate(self.site, 'basic-changing')
        self.outputpage = outputpage
        self.maxlines = maxlines

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
        textload = self.load(page)
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

        ################################################################
        # NOTE: Here you can modify the text in whatever way you want. #
        ################################################################

       
    def load(self, page):
        """
        Loads the given page, does some changes, and saves it.
        """
        try:
            # Load the page
            text = page.get()
        except pywikibot.NoPage:
            pywikibot.output(u"Page %s does not exist; skipping."
                             % page.title(asLink=True))
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"Page %s is a redirect; skipping."
                             % page.title(asLink=True))
        else:
            return text
        return None

    def save(self, text, page, comment=None, minorEdit=True,
             botflag=True):
        # only save if something was changed
        try:        
	   pagetext = page.get()
        except:
           pagetext = u''
        if text != pagetext:
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                             % page.title())
            # show what was changed
            pywikibot.showDiff(pagetext, text)
            pywikibot.output(u'Comment: %s' %comment)
            #choice = pywikibot.inputChoice(
            #    u'Do you want to accept these changes?',
            #    ['Yes', 'No'], ['y', 'N'], 'N')
            try:
                    # Save the page
                    page.put(text, comment=comment or self.comment,
                             minorEdit=minorEdit, botflag=botflag)
            except pywikibot.LockedPage:
                    pywikibot.output(u"Page %s is locked; skipping."
                                     % page.title(asLink=True))
            except pywikibot.EditConflict:
                    pywikibot.output(
                        u'Skipping %s because of edit conflict'
                        % (page.title()))
            except pywikibot.SpamfilterError, error:
                    pywikibot.output(u'Cannot change %s because of spam blacklist entry %s'
                        % (page.title(), error.url))
            else:
                    return True
        return False

class AutoBasicBot(BasicBot):
    # Intended for usage e.g. as cronjob without prompting the user.

    _REGEX_eol = re.compile(u'\n')

    def __init__(self):
        BasicBot.__init__(self, None, None)

    ## @since   10326
    #  @remarks needed by various bots
    def save(self, page, text, comment=None, minorEdit=True, botflag=True):
        pywikibot.output(u'\03{lightblue}Writing to wiki on %s...\03{default}' % page.title(asLink=True))

        comment_output = comment or pywikibot.action
        pywikibot.output(u'\03{lightblue}Comment: %s\03{default}' % comment_output)

        #pywikibot.showDiff(page.get(), text)

        for i in range(3): # try max. 3 times
            try:
                # Save the page
                page.put(text, comment=comment, minorEdit=minorEdit, botflag=botflag)
            except pywikibot.LockedPage:
                pywikibot.output(u"\03{lightblue}Page %s is locked; skipping.\03{default}" % page.title(asLink=True))
            except pywikibot.EditConflict:
                pywikibot.output(u'\03{lightblue}Skipping %s because of edit conflict\03{default}' % (page.title()))
            except pywikibot.SpamfilterError, error:
                pywikibot.output(u'\03{lightblue}Cannot change %s because of spam blacklist entry %s\03{default}' % (page.title(), error.url))
            else:
                return True
        return False

    ## @since   10326
    #  @remarks needed by various bots
    def append(self, page, text, comment=None, minorEdit=True, section=None):
        if section:
            pywikibot.output(u'\03{lightblue}Appending to wiki on %s in section %s...\03{default}' % (page.title(asLink=True), section))

            for i in range(3): # try max. 3 times
                try:
                    # Append to page section
                    page.append(text, comment=comment, minorEdit=minorEdit, section=section)
                except pywikibot.PageNotSaved, error:
                    pywikibot.output(u'\03{lightblue}Cannot change %s because of %s\03{default}' % (page.title(), error))
                else:
                    return True
        else:
            content = self.load( page )     # 'None' if not existing page
            if not content:                 # (create new page)
                content = u''

            content += u'\n\n'
            content += text

            return self.save(page, content, comment=comment, minorEdit=minorEdit)

    ## @since   10326
    #  @remarks needed by various bots
    def loadTemplates(self, page, template, default={}):
        """Get operating mode from page with template by searching the template.

           @param page: The user (page) for which the data should be retrieved.

           Returns a list of dict with the templates parameters found.
        """

        self._content = self.load(page) # 'None' if not existing page

        templates = []
        if not self._content:
            return templates  # catch empty or not existing page

        for tmpl in pywikibot.extract_templates_and_params(self._content):
            if tmpl[0] == template:
                param_default = {}
                param_default.update(default)
                param_default.update(tmpl[1])
                templates.append( param_default )
        return templates

    ## @since   10326
    #  @remarks common interface to bot job queue on wiki
    def loadJobQueue(self, page, queue_security, reset=True):
        """Check if the data queue security is ok to execute the jobs,
           if so read the jobs and reset the queue.

           @param page: Wiki page containing job queue.
           @type  page: page
           @param queue_security: This string must match the last edit
                              comment, or else nothing is done.
           @type  queue_security: string

           Returns a list of jobs. This list may be empty.
        """

        try:    actual = page.getVersionHistory(revCount=1)[0]
        except:    pass

        secure = False
        for item in queue_security[0]:
            secure = secure or (actual[2] == item)

        secure = secure and (actual[3] == queue_security[1])

        if not secure: return []

        data = self._REGEX_eol.split(page.get())
        if reset:
            pywikibot.output(u'\03{lightblue}Job queue reset...\03{default}')
            
            pywikibot.setAction(u'reset job queue')
            page.put(u'', minorEdit = True)

        queue = []
        for line in data:
            queue.append( line[1:].strip() )
        return queue

def main():
    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()
    # The generator gives the pages that should be worked upon.
    gen = None
    # This temporary array is used to read the page title if one single
    # page to work on is specified by the arguments.
    pageTitleParts = []
    # summary message
    editSummary = ''
    outPage = 'User:MastiBot/test'
    maxLines = 1000

    # Parse command line arguments
    for arg in pywikibot.handleArgs():
        if arg.startswith('-summary:'):
            editSummary = arg[9:]
        elif arg.startswith('-outpage:'):
            outPage = arg[9:]
        elif arg.startswith('-maxlines:'):
            maxLines = int(arg[10:])
        else:
            # check if a standard argument like
            # -start:XYZ or -ref:Asdf was given.
            if not genFactory.handleArg(arg):
                pageTitleParts.append(arg)

    if pageTitleParts != []:
        # We will only work on a single page.
        pageTitle = ' '.join(pageTitleParts)
        page = pywikibot.Page(pywikibot.getSite(), pageTitle)
        gen = iter([page])

    if not gen:
        gen = genFactory.getCombinedGenerator()
    if gen:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        gen = pagegenerators.PreloadingGenerator(gen)
        bot = BasicBot(gen, editSummary, outPage, maxLines)
        bot.run()
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
