#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot creates a pages with current results of various votings on pl.wikipedia

Call: time python pwb.py masti/m-votes.py -page:'!' -outpage:'votes.html'; cp ~/pw/core/masti/html/votes.html ~/public_html/votes.html

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
import urllib
import urllib2
from datetime import datetime
from time import strftime
import difflib


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}
voteResults = {}

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
            'test': False, #switch on test functionality
            'KA': False, #switch on ArbCom voting
            'KAmonth': None, #ArbCom voting month eg. 2017-09
            'KAplaces': 4, #ArbCom plac to be won
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

        
        if self.getOption('KA'):  
            #KAvotesResult = self.KAvotes(u'Wikipedia:Komitet Arbitrażowy/Wybór członków/' + self.getOption('KAmonth') + u'/Całość')
            KAvotesResult = self.KAvotes(u'Wikipedysta:masti/KA')
            if KAvotesResult:
                voteResults['KA'] = KAvotesResult
                # test only
                #pywikibot.output(u'KAvotesResult: %s' % KAvotesResult)
        
        """
        #PUvotesResult = self.PUvotes(u'Wikipedysta:MastiBot/Przyznawanie_uprawnień')
        PUvotesResult = self.PUvotes(u'Wikipedia:Przyznawanie_uprawnień')
        if PUvotesResult:
            voteResults['PU'] = PUvotesResult
            if self.getOption('test'):
	        pywikibot.output(u'PUvotesResult: %s' % PUvotesResult)
        
        PDAvotesResult = self.PDAvotes(u'Wikipedia:Propozycje do Dobrych Artykułów', u'PDA')
        if PDAvotesResult:
            voteResults['PDA'] = PDAvotesResult
            if self.getOption('test'):
                pywikibot.output(u'PDAvotesResult: %s' % PDAvotesResult)
        
        PAMvotesResult = self.PDAvotes(u'Wikipedia:Propozycje do Artykułów na medal', u'PAM')
        if PAMvotesResult:
            voteResults['PAM'] = PAMvotesResult
            if self.getOption('test'):
                pywikibot.output(u'PAMvotesResult: %s' % PAMvotesResult)
        
        INMvotesResult = self.INMvotes(u'Wikipedia:Ilustracja na medal - propozycje')
        if INMvotesResult:
            voteResults['INM'] = INMvotesResult
            if self.getOption('test'):
                pywikibot.output(u'INMvotesResult: %s' % INMvotesResult)

        LNMvotesResult = self.LNMvotes(u'Wikipedia:Propozycje do List na medal')
        if LNMvotesResult:
            voteResults['LNM'] = LNMvotesResult
            if self.getOption('test'):
                pywikibot.output(u'LNMvotesResult: %s' % LNMvotesResult)

        PDGAvotesResult = self.PDGAvotes(u'Wikipedia:Propozycje do Grup Artykułów')
        if PDGAvotesResult:
            voteResults['PDGA'] = PDGAvotesResult
            if self.getOption('test'):
                pywikibot.output(u'LNMvotesResult: %s' % LNMvotesResult)
        """

        pywikibot.output(u'voteResults: %s' % voteResults)

        self.generateresultspage( voteResults )

        if self.getOption('test'):
            pywikibot.output(u'****END OF PROGRAM***')

    """
    KA related part
    """

    """
    Tylko na czas wyborów
    """
    def KAvotes(self, pagename):
        #generate Przyznawanie uprawnień page list of voting subpages as list
        #test
        #pywikibot.output(u'***KAvotes')
        votesL = []
        votespage = pywikibot.Page(pywikibot.Site(), pagename)
        text = votespage.text
        if not text:
            return(None)
        #kaR = re.compile(ur'\{\{Wikipedia:Komitet Arbitrażowy\/Wybór członków\/' + self.getOption('KAmonth') + u'\/(?P<puname>.*)}}')
        kaR = re.compile(ur'\{\{\/(?P<puname>.*)}}')
        if self.getOption('test'):
            pywikibot.output(u'kaR: %s' % kaR)
        kafound = False
        kalist = kaR.finditer(text)
        for ka in kalist:
            subpage = ka.group('puname').strip()
            #test
	    #pywikibot.output(subpage)
            if not u'Całość' in subpage:
               kafound = True
               votesL.append(self.KASingleVote(subpage))
               # test
               #pywikibot.output(u'Subpage: %s votesL: %s' % (subpage, votesL[len(votesL)-1]))

        return(votesL)

    def KASingleVote(self, pagename):
        #generate Single Vote result as tuple (wikipedysta, error, (za, przeciw,  neutral, netto, %))
        if self.getOption('test'):
            pywikibot.output(u'****generateKAvoteresult:' + pagename)
        #votespage = pywikibot.Page(pywikibot.Site(), u'Wikipedia:Komitet Arbitrażowy/Wybór członków/' + self.getOption('KAmonth') + u'/' + pagename)
        votespage = pywikibot.Page(pywikibot.Site(), u'Wikipedysta:masti/KA/' + pagename)
        text = votespage.text
        if not text:
            return(None)

        #removeDisabledParts
        text = pywikibot.textlib.removeDisabledParts(text)
        if self.getOption('test'):
            pywikibot.output(u'Vote text:\n%s' % text)

        # vote counting regexp
        forR = re.compile(ur'={4}\s*?Za:?\s*?={4}\n(?P<forvotes>.*?)={4}',re.S)
        againstR = re.compile(ur'={4}\s*?Przeciw:?\s*?={4}\n(?P<againstvotes>.*?)={4}',re.S)
        abstainR = re.compile(ur'={4}\s*?Wstrzymuję się:?\s*?={4}\n(?P<abstainvotes>.*?)={4}',re.S)
        try:
            # count For votes
            votesection = forR.search(text).group('forvotes')
            #pywikibot.output(u'Vote section: %s' % votesection)
            forvotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'For votes count: %i' % forvotes)

            # count Against votes
            votesection = againstR.search(text).group('againstvotes')
            #pywikibot.output(u'Vote section: %s' % votesection)
            againstvotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'Against votes count: %i' % againstvotes)

            # count Abstain votes
            votesection = abstainR.search(text).group('abstainvotes')
            #pywikibot.output(u'Vote section: %s' % votesection)
            abstainvotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'Abstain votes count: %i' % abstainvotes)

            #pywikibot.output(u'Sumvotes: %i' % forvotes + againstvotes)
            if forvotes + againstvotes > 0:
                percentvotes = forvotes / float(forvotes + againstvotes)
            else:
                percentvotes = 0
            if self.getOption('test'):
                #pywikibot.output(u'Sum of votes count: %i' % sumvotes)
                pywikibot.output(u'Percentage: %f' % percentvotes)
            return( (pagename, False, (forvotes, againstvotes, abstainvotes, forvotes-againstvotes, percentvotes)) )
        except:
            pywikibot.output(u'***ERROR - cannot analyse votes: %s' % pagename)
            return( (pagename, True, ()) )
    

        
    """
    PU related part
    """

    def PUvotes(self, pagename):
        #generate Przyznawanie uprawnień page list of voting subpages as list
        if self.getOption('test'):
            pywikibot.output(u'***PUvotes')
        votesL = []
        votespage = pywikibot.Page(pywikibot.Site(), pagename)
        text = votespage.text
        if not text:
            return(None)
        puR = re.compile(ur'\{\{Wikipedia:Przyznawanie uprawnień\/(?P<puname>.*)}}')
        pufound = False
        pulist = puR.finditer(text)
        for pu in pulist:
            subpage = pu.group('puname').strip()
            if self.getOption('test'):
                pywikibot.output(subpage)
            if not u'Wstęp' in subpage:
               pufound = True
               votesL.append(self.PUSingleVote(subpage))
               if self.getOption('test'):
                   pywikibot.output(u'Subpage: %s votesL: %s' % (subpage, votesL[len(votesL)-1]))

        return(votesL)

    def PUSingleVote(self, pagename):
        #generate Single Vote result as tuple (wikipedysta, error, (za, przeciw,  neutral, netto, %, data))
        if self.getOption('test'):
            pywikibot.output(u'****generatePUvoteresult:' + pagename)
        votespage = pywikibot.Page(pywikibot.Site(), u'Wikipedia:Przyznawanie uprawnień/' + pagename)
        text = votespage.text
        if not text:
            return(None)

        # find end of voting string
        try:
            eovR = re.compile(ur'\{\{Ramy czasowe zdarzenia.*?stop\s*?=\s*?(?P<eofv>.*?)\|')
            endofvotinglist = eovR.search(text)
            endofvoting = endofvotinglist.group('eofv').strip()
            if self.getOption('test'):
                pywikibot.output(u'End of Voting: %s' % endofvoting)
        except:
            endofvoting = u'brak danych'

        #removeDisabledParts
        text = pywikibot.textlib.removeDisabledParts(text)
        if self.getOption('test'):
            pywikibot.output(u'Vote text:\n%s' % text)

        # vote counting regexp
        forR = re.compile(ur'={4}\s*?Za\s*?={4}\n(?P<forvotes>.*?)={4}',re.S)
        againstR = re.compile(ur'={4}\s*?Przeciw\s*?={4}\n(?P<againstvotes>.*?)={4}',re.S)
        abstainR = re.compile(ur'={4}\s*?Wstrzymuję się\s*?={4}\n(?P<abstainvotes>.*?)={4}',re.S)
        try:
            # count For votes
            votesection = forR.search(text).group('forvotes')
            #pywikibot.output(u'Vote section: %s' % votesection)
            forvotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'For votes count: %i' % forvotes)

            # count Against votes
            votesection = againstR.search(text).group('againstvotes')
            #pywikibot.output(u'Vote section: %s' % votesection)
            againstvotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'Against votes count: %i' % againstvotes)

            # count Abstain votes
            votesection = abstainR.search(text).group('abstainvotes')
            #pywikibot.output(u'Vote section: %s' % votesection)
            abstainvotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'Abstain votes count: %i' % abstainvotes)

            if forvotes + againstvotes > 0:
                percentvotes = forvotes / float(forvotes + againstvotes)
            else:
                percentvotes = 0
            if self.getOption('test'):
                #pywikibot.output(u'Sum of votes count: %i' % sumvotes)
                pywikibot.output(u'Percentage: %f' % percentvotes)
            return( (pagename, False, (forvotes, againstvotes, abstainvotes, forvotes-againstvotes, percentvotes, endofvoting)) )
        except:
            pywikibot.output(u'***ERROR - cannot analyse votes: %s' % pagename)
            return( (pagename, True, ()) )

    def CountVotes(self, voteslist):
        #count votes in list
        if self.getOption('test'):
            pywikibot.output(u'****CountVotes:' + voteslist)
        #voteR = re.compile(ur'#(\s*?[^\s\n;#]+)')
        voteR = re.compile(ur'^#[^:](?P<vote>[^\n]*)', re.M)
        voteL = voteR.finditer(voteslist)
        count = 0
        for v in voteL:
           if v.group('vote'):
               count += 1

        return( count )

    """
    PDA related part
    """
    def PDAvotes(self, pagename, pdapam):
        #generate Propozycje do Dobrych Artykułów page list of voting subpages as list
        if self.getOption('test'):
            pywikibot.output(u'***PDAvotes')
        votesL = []
        votespage = pywikibot.Page(pywikibot.Site(), pagename)
        text = votespage.text
        if not text:
            return(None)
        pdaR = re.compile(ur'\{\{(Wikipedia:Propozycje do Dobrych Artykułów|Wikipedia:Propozycje do Artykułów na medal)?\/(?P<subpage>.*?)}}')
        pdafound = False
        pdalist = pdaR.finditer(text)
        for pda in pdalist:
            subpage = pda.group('subpage').strip()
            if self.getOption('test'):
                pywikibot.output(subpage)
            if (not subpage.startswith(u'przyznawanie')) and (not subpage.startswith(u'weryfikacja')):
                pdafound = True
                votesL.append(self.PDASingleVote(subpage, pdapam))
                if self.getOption('test'):
                    pywikibot.output(u'Subpage: %s votesL: %s' % (subpage, votesL[len(votesL)-1]))

        return(votesL)

    def PDASingleVote(self, pagename, pdapam):
        #generate Single Vote result as tuple (strona, error, (sprawdzający, data))
        if self.getOption('test'):
            pywikibot.output(u'****generatePDAvoteresult:' + pagename)
        if u'PDA' in pdapam:
            votespage = pywikibot.Page(pywikibot.Site(), u'Wikipedia:Propozycje do Dobrych Artykułów/' + pagename)
            #votespage = pywikibot.Page(pywikibot.Site(), u'Wikipedysta:MastiBot/test')
        else:
            votespage = pywikibot.Page(pywikibot.Site(), u'Wikipedia:Propozycje do Artykułów na medal/' + pagename)
        text = votespage.text
        if not text:
            return(None)

        # find end of voting string
        try:
            eovR = re.compile(ur'\{\{Ramy czasowe zdarzenia.*?stop\s*?=\s*?(?P<eofv>.*?)\|')
            endofvotinglist = eovR.search(text)
            endofvoting = endofvotinglist.group('eofv').strip()
            if self.getOption('test'):
                pywikibot.output(u'End of Voting: %s' % endofvoting)
        except:
            endofvoting = u'brak danych'

        #removeDisabledParts
        text = pywikibot.textlib.removeDisabledParts(text)
        if self.getOption('test'):
            pywikibot.output(u'Vote text:\n%s' % text)

        # vote counting regexp
        verR = re.compile(ur'; Sprawdzone przez\s*?\n+(?P<verifiers>.*)', re.S)
        try:
            # count verifiers votes
            votesection = verR.search(text).group('verifiers')
            if self.getOption('test'):
                pywikibot.output(u'Vote section: %s' % votesection)
            vervotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'Ver votes count: %i' % vervotes)
            return( (pagename, False, (vervotes, endofvoting)) )
        except:
            pywikibot.output(u'***ERROR - cannot analyse votes: %s' % pagename)
            return( (pagename, True, ()) )

    """
    INM related part
    """
    def INMvotes(self, pagename):
        #generate Wikipedia:Ilustracja na medal - propozycje page list of voting subpages as list
        if self.getOption('test'):
            pywikibot.output(u'***INMvotes')
        votesL = []
        votespage = pywikibot.Page(pywikibot.Site(), pagename)
        text = votespage.text
        if not text:
            return(None)
        inmR = re.compile(ur'\{\{(Wikipedia:Ilustracja na medal - propozycje)?\/(?P<subpage>.*?)}}')
        inmfound = False
        inmlist = inmR.finditer(text)
        for inm in inmlist:
            subpage = inm.group('subpage').strip()
            if self.getOption('test'):
                pywikibot.output(subpage)
            if (not subpage.startswith(u'Zasady')) and (not subpage.startswith(u'Instrukcja')):
                inmfound = True
                votesL.append(self.INMSingleVote(subpage))
                if self.getOption('test'):
                    pywikibot.output(u'Subpage: %s votesL: %s' % (subpage, votesL[len(votesL)-1]))

        return(votesL)

    def INMSingleVote(self, pagename):
        #generate Single Vote result as tuple (strona, error, (za, przeciw, netto, procent, data))
        if self.getOption('test'):
            pywikibot.output(u'****generatePDAvoteresult:' + pagename)
        votespage = pywikibot.Page(pywikibot.Site(), u'Wikipedia:Ilustracja na medal - propozycje/' + pagename)
        text = votespage.text
        if not text:
            return(None)

        # find end of voting string
        try:
            eovR = re.compile(ur'\{\{Ramy czasowe zdarzenia.*?stop\s*?=\s*?(?P<eofv>.*?)\|')
            endofvotinglist = eovR.search(text)
            endofvoting = endofvotinglist.group('eofv').strip()
            if self.getOption('test'):
                pywikibot.output(u'End of Voting: %s' % endofvoting)
        except:
            endofvoting = u'brak danych'

        # vote counting regexp
        forR = re.compile(ur"\*\s*?'''Głosy za( odebraniem medalu)?:'''\s*?\n+(?P<forvotes>.*?)\n\*\s*?'''", re.S)
        againstR = re.compile(ur"\*\s*?'''Głosy przeciw( odebraniu medalu)?:'''\s*?\n+(?P<againstvotes>.*?)\n\*\s*?'''", re.S)

        #removeDisabledParts
        text = pywikibot.textlib.removeDisabledParts(text)
        if self.getOption('test'):
            pywikibot.output(u'Vote text:\n%s' % text)

        try:
            # count For votes
            votesection = forR.search(text).group('forvotes')
            #pywikibot.output(u'Vote section: %s' % votesection)
            forvotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'For votes count: %i' % forvotes)

            # count Against votes
            votesection = againstR.search(text).group('againstvotes')
            #pywikibot.output(u'Vote section: %s' % votesection)
            againstvotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'Against votes count: %i' % againstvotes)

            #calculate netto
            netto = forvotes - againstvotes
            if self.getOption('test'):
                pywikibot.output(u'Netto votes count: %i' % netto)

            #calculate percentage
            if forvotes + againstvotes > 0:
                percentvotes = forvotes / float(forvotes + againstvotes)
            else:
                percentvotes = 0
            if self.getOption('test'):
                #pywikibot.output(u'Sum of votes count: %i' % sumvotes)
                pywikibot.output(u'Percentage: %f' % percentvotes)

            return( (pagename, False, (forvotes, againstvotes, netto, percentvotes, endofvoting)) )
        except:
            pywikibot.output(u'***ERROR - cannot analyse votes: %s' % pagename)
            return( (pagename, True, ()) )

    """
    LNM related part
    """
    def LNMvotes(self, pagename):
        #generate Wikipedia:Propozycje do List na medal page list of voting subpages as list
        #test
        #pywikibot.output(u'***LNMvotes')
        votesL = []
        votespage = pywikibot.Page(pywikibot.Site(), pagename)
        text = votespage.text
        if not text:
            return(None)
        #test
        #pywikibot.output(u'*** LNM:\n%s' % text)
        lnmR = re.compile(ur'\{\{(Wikipedia:Propozycje do List na medal)?\/(?P<subpage>.*?)}}')
        lmfound = False
        lnmlist = lnmR.finditer(text)
        for lnm in lnmlist:
            subpage = lnm.group('subpage').strip()
	    #test
            #pywikibot.output(subpage)
            if (not subpage.startswith(u'przyznawanie')) and (not subpage.startswith(u'weryfikacja') ) :
               lnmfound = True
               votesL.append(self.LNMSingleVote(subpage))
               # test
               #pywikibot.output(u'Subpage: %s votesL: %s' % (subpage, votesL[len(votesL)-1]))

        return(votesL)

    def LNMSingleVote(self, pagename):
        #generate Single Vote result as tuple (strona, error, (za, przeciw, netto, procent, data))
        if self.getOption('test'):
            pywikibot.output(u'****generateLNMvoteresult:' + pagename)
        votespage = pywikibot.Page(pywikibot.Site(), u'Wikipedia:Propozycje do List na medal/' + pagename)
        text = votespage.text
        if not text:
            return(None)

        # find end of voting string
        try:
            eovR = re.compile(ur'\{\{Ramy czasowe zdarzenia.*?stop\s*?=\s*?(?P<eofv>.*?)\|')
            endofvotinglist = eovR.search(text)
            endofvoting = endofvotinglist.group('eofv').strip()
            if self.getOption('test'):
                pywikibot.output(u'End of Voting: %s' % endofvoting)
        except:
            endofvoting = u'brak danych'

        # vote counting regexp
        forR = re.compile(ur"\*\s*?'''Głosy za:'''\s*?\n+(?P<forvotes>.*?)\n\*\s*?'''", re.S)
        againstR = re.compile(ur"\*\s*?'''Głosy przeciw:'''\s*?\n+(?P<againstvotes>.*?)\n\*\s*?'''", re.S)
        
        #removeDisabledParts
        text = pywikibot.textlib.removeDisabledParts(text)
        if self.getOption('test'):
            pywikibot.output(u'Vote text:\n%s' % text)

        forvotes = ''
        againstvotes = ''
        netto = ''
        percentvotes = ''

        try:
            # count For votes
            votesection = forR.search(text).group('forvotes')
            #pywikibot.output(u'Vote section: %s' % votesection)
            forvotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'For votes count: %i' % forvotes)

            # count Against votes
            votesection = againstR.search(text).group('againstvotes')
            #pywikibot.output(u'Vote section: %s' % votesection)
            againstvotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'Against votes count: %i' % againstvotes)

            #calculate netto
            netto = forvotes - againstvotes
            if self.getOption('test'):
                pywikibot.output(u'Netto votes count: %i' % netto)

            #calculate percentage
            if forvotes + againstvotes > 0:
                percentvotes = forvotes / float(forvotes + againstvotes)
            else:
                percentvotes = 0
            if self.getOption('test'):
                #pywikibot.output(u'Sum of votes count: %i' % sumvotes)
                pywikibot.output(u'Percentage: %f' % percentvotes)

            return( (pagename, False, (forvotes, againstvotes, netto, percentvotes, endofvoting)) )
        except:
            pywikibot.output(u'***ERROR - cannot analyse votes: %s' % pagename)
            return( (pagename, True, ()) )

    """
    PDGA related part
    """
    def PDGAvotes(self, pagename):
        #generate Wikipedia:Propozycje do Grup Artykułów page list of voting subpages as list
        #test
        #pywikibot.output(u'***PDGAvotes')
        votesL = []
        votespage = pywikibot.Page(pywikibot.Site(), pagename)
        text = votespage.text
        if not text:
            return(None)

        #removeDisabledParts
        text = pywikibot.textlib.removeDisabledParts(text)
        if self.getOption('test'):
            pywikibot.output(u'Vote text:\n%s' % text)


        if self.getOption('test'):
            pywikibot.output(u'*** PDGA:\n%s' % text)
        pdgaR = re.compile(ur'\{\{(Wikipedia:Propozycje do Grup Artykułów)?\/(?P<subpage>.*?)}}')
        pdgafound = False
        pdgalist = pdgaR.finditer(text)
        for pdga in pdgalist:
            subpage = pdga.group('subpage').strip()
            if self.getOption('test'):
                pywikibot.output(subpage)
            if (not subpage.startswith(u'przyznawanie')) and (not subpage.startswith(u'weryfikacja') ) :
                pdgafound = True
                votesL.append(self.PDGASingleVote(subpage))
                if self.getOption('test'):
                    pywikibot.output(u'Subpage: %s votesL: %s' % (subpage, votesL[len(votesL)-1]))

        return(votesL)

    def PDGASingleVote(self, pagename):
        #generate Single Vote result as tuple (strona, error, (za, przeciw, netto, procent, data))
        if self.getOption('test'):
            pywikibot.output(u'****generateLNMvoteresult:' + pagename)
        votespage = pywikibot.Page(pywikibot.Site(), u'Wikipedia:Propozycje do Grup Artykułów/' + pagename)
        text = votespage.text
        if not text:
            return(None)

        # find end of voting string
        try:
            eovR = re.compile(ur'\{\{Ramy czasowe zdarzenia.*?stop\s*?=\s*?(?P<eofv>.*?)\|')
            endofvotinglist = eovR.search(text)
            endofvoting = endofvotinglist.group('eofv').strip()
            if self.getOption('test'):
                pywikibot.output(u'End of Voting: %s' % endofvoting)
        except:
            endofvoting = u'brak danych'

        # vote counting regexp
        forR = re.compile(ur"\*\s*?'''Głosy za:'''\s*?\n+(?P<forvotes>.*?)\n\*\s*?'''", re.S)
        againstR = re.compile(ur"\*\s*?'''Głosy przeciw:'''\s*?\n+(?P<againstvotes>.*?)\n\*\s*?'''", re.S)
        
        #removeDisabledParts
        text = pywikibot.textlib.removeDisabledParts(text)
        if self.getOption('test'):
            pywikibot.output(u'Vote text:\n%s' % text)

        forvotes = ''
        againstvotes = ''
        netto = ''
        percentvotes = ''

        try:
            # count For votes
            votesection = forR.search(text).group('forvotes')
            #pywikibot.output(u'Vote section: %s' % votesection)
            forvotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'For votes count: %i' % forvotes)

            # count Against votes
            votesection = againstR.search(text).group('againstvotes')
            #pywikibot.output(u'Vote section: %s' % votesection)
            againstvotes = self.CountVotes(votesection)
            if self.getOption('test'):
                pywikibot.output(u'Against votes count: %i' % againstvotes)

            #calculate netto
            netto = forvotes - againstvotes
            if self.getOption('test'):
                pywikibot.output(u'Netto votes count: %i' % netto)

            #calculate percentage
            if forvotes + againstvotes > 0:
                percentvotes = forvotes / float(forvotes + againstvotes)
            else:
                percentvotes = 0
            if self.getOption('test'):
                #pywikibot.output(u'Sum of votes count: %i' % sumvotes)
                pywikibot.output(u'Percentage: %f' % percentvotes)

            return( (pagename, False, (forvotes, againstvotes, netto, percentvotes, endofvoting)) )
        except:
            pywikibot.output(u'***ERROR - cannot analyse votes: %s' % pagename)
            return( (pagename, True, ()) )
        


    """
    Main page related part
    """

    def mainheader(self):
        #prepare main page header
        header = u'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'
        header += u'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pl" lang="pl" dir="ltr">\n'
        header += u'	<head>\n'
        header += u'		<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n'
        header += u'		<title>Głosowania - tools.wikimedia.pl</title>\n'
        header += u'		<link rel="stylesheet" type="text/css" href="/~masti/modern.css" />\n'
        #header += u'		<style type="text/css">\n'
        #header += u'table.wikitable td, table.wikitable th {\n'
        #header += u'	padding: 5px;\n'
        #header += u'}\n'
        #header += u'table.wikitable tr:nth-child(odd) {\n'
        #header += u'	background-color: #F9F9F9;\n'
        #header += u'}\n'
        #header += u'		</style>\n'
        header += u'	</head>\n'
        header += u'<body>\n'
        header += u'\n'
        header += u'	<!-- heading -->\n'
        header += u'	<div id="mw_header">\n'
        header += u'		<h1 id="firstHeading">Głosowania</h1>\n'
        header += u'	</div>\n'
        header += u'\n'
        header += u'	<div id="mw_main">\n'
        header += u'	<div id="mw_contentwrapper">\n'
        header += u'\n'
        header += u'	<!-- content -->\n'
        header += u'	<div id="mw_content">\n'
        header += u'\n'
        header += u'	<p>Rzeczywiste wyniki mogą się różnić od podanych poniżej (ktoś może nie mieć prawa głosu, zagłosować w nieprawidłowy sposób lub źle skomentować czyjś głos)! Strona jest aktualizowana co pięć minut.</p>\n'
        header += u'	<p><small>Komunikat <i>nie można odczytać danych</i> pojawia się w dwóch przypadkach:\n'
        header += u'		<ul>\n'
        header += u'			<li>na liście głosowań jest podlinkowane przekierowanie, a nie strona głosowania,</li>\n'
        header += u'			<li>domyślny układ głosowania został zmieniony (bot nie może znaleźć sekcji z głosami).</li>\n'
        header += u'		</ul>\n'
        header += u'	</small></p>\n'
        #header += u'	<p><center>***** Statystyki są w fazie eksperymentalnej. Wszelkie zauważone problemy proszę zgłaszać w <a href="http://pl.wikipedia.org/wiki/Dyskusja_wikipedysty:masti">dyskusji operatora.</a> *****</center>\n'
        #header += u'	</p>\n'
        # add creation time
        header += u'	<p>Ostatnia aktualizacja: <b>' + strftime('%A %d %B %Y %X %Z').encode('UTF-8') + u'</b></p>\n'
        header += u'\n'
        #header += u'	<p><center><FORM>\n'
        #header += u'	<INPUT TYPE="button" onClick="history.go(0)" VALUE="ODŚWIEŻ">\n'
        #header += u'	</FORM>\n'
        #header += u'	</center></p>\n'
        header += u'<center><b><a class="external text" href="http://tools.wikimedia.pl/~masti/' + self.getOption('outpage') + u'">ODŚWIEŻ</a></b></center>'

        return(header)

    def mainfooter(self):
        #prepare main page footer
        footer = u'	</div><!-- mw_content -->\n'
        footer += u'	</div><!-- mw_contentwrapper -->\n'
        footer += u'\n'
        footer += u'	</div><!-- main -->\n'
        footer += u'\n'
        footer += u'	<div class="mw_clear"></div>\n'
        footer += u'\n'
        footer += u'	<!-- personal portlet -->\n'
        footer += u'	<div class="portlet" id="p-personal">\n'
        footer += u'		<div class="pBody">\n'
        footer += u'			<ul>\n'
        footer += u'				<li><a href="http://pl.wikipedia.org">wiki</a></li>\n'
        footer += u'				<li><a href="/">tools</a></li>\n'
        footer += u'				<li><a href="/~masti/">masti</a></li>\n'
        footer += u'			</ul>\n'
        footer += u'		</div>\n'
        footer += u'		</div>\n'
        footer += u'<div class="stopka">layout by <a href="../~beau/">Beau</a></div>\n'
        footer += u'</body></html>\n'

        return(footer)

        '''
        KA section
        '''

    def KAheader(self):
        header = u'	<h2><a name="ka"></a>Komitet Arbitrażowy</h2>\n'
        header += u'	<div class="detail"><a href="//pl.wikipedia.org/wiki/Plik:Information_icon.svg" class="image" title="Information icon.svg"><img alt="" src="//upload.wikimedia.org/wikipedia/commons/thumb/3/35/Information_icon.svg/15px-Information_icon.svg.png" border="0" height="15" width="15"></a> <i>Zobacz więcej na osobnej stronie: <a href="//pl.wikipedia.org/wiki/Wikipedia:Komitet_Arbitra%C5%BCowy/Wyb%C3%B3r_cz%C5%82onk%C3%B3w/' + self.getOption('KAmonth') + u'" title="Wikipedia:Komitet Arbitrażowy/Wybór członków/' + self.getOption('KAmonth') + u'">Wikipedia:Komitet Arbitrażowy/Wybór członków/' + self.getOption('KAmonth') + u'</a>.</i></div>\n'

        return(header)

    def KAtableheader(self):
        header = u'	<table class="votestable">\n'
        header += u'		<tr>\n'
        header += u'			<th>Pozycja</th>\n'
        header += u'			<th>wikipedysta</th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:Symbol_support_vote.svg" class="image" title="Liczba głosów za"><img alt="+" src="//upload.wikimedia.org/wikipedia/commons/thumb/9/94/Symbol_support_vote.svg/15px-Symbol_support_vote.svg.png" border="0" height="15" width="15"></a></th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:Symbol_oppose_vote.svg" class="image" title="Liczba głosów przeciw"><img alt="-" src="//upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Symbol_oppose_vote.svg/15px-Symbol_oppose_vote.svg.png" border="0" height="15" width="15"></a></th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:Symbol_neutral_vote.svg" class="image" title="Liczba głosów wstrzymuję się"><img alt="?" src="//upload.wikimedia.org/wikipedia/commons/thumb/8/89/Symbol_neutral_vote.svg/15px-Symbol_neutral_vote.svg.png" border="0" height="15" width="15"></a></th>\n'
        header += u'			<th>netto</th>\n'
        header += u'			<th>%</th>\n'
        header += u'		</tr>\n'

        return(header)

    def KAtablefooter(self):
        footer = u'	</table>\n'

        return(footer)

        '''
        PU section
        '''

    def PUheader(self):
        header = u'	<h2><a name="pu"></a>Przyznawanie uprawnień</h2>\n'
        header += u'	<div class="detail"><a href="//pl.wikipedia.org/wiki/Plik:Information_icon.svg" class="image" title="Information icon.svg"><img alt="" src="//upload.wikimedia.org/wikipedia/commons/thumb/3/35/Information_icon.svg/15px-Information_icon.svg.png" border="0" height="15" width="15"></a> <i>Zobacz więcej na osobnej stronie: <a href="//pl.wikipedia.org/wiki/Wikipedia%3APrzyznawanie%20uprawnie%C5%84" title="Wikipedia:Przyznawanie uprawnień">Wikipedia:Przyznawanie uprawnień</a>.</i></div>\n'

        return(header)

    def PUtableheader(self):
        header = u'	<table class="wikitable vote">\n'
        header += u'		<tr>\n'
        header += u'			<th>wikipedysta</th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:Symbol_support_vote.svg" class="image" title="Liczba głosów za"><img alt="+" src="//upload.wikimedia.org/wikipedia/commons/thumb/9/94/Symbol_support_vote.svg/15px-Symbol_support_vote.svg.png" border="0" height="15" width="15"></a></th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:Symbol_oppose_vote.svg" class="image" title="Liczba głosów przeciw"><img alt="-" src="//upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Symbol_oppose_vote.svg/15px-Symbol_oppose_vote.svg.png" border="0" height="15" width="15"></a></th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:Symbol_neutral_vote.svg" class="image" title="Liczba głosów wstrzymuję się"><img alt="?" src="//upload.wikimedia.org/wikipedia/commons/thumb/8/89/Symbol_neutral_vote.svg/15px-Symbol_neutral_vote.svg.png" border="0" height="15" width="15"></a></th>\n'
        header += u'			<th>netto</th>\n'
        header += u'			<th>%</th>\n'
        header += u'			<th>data zakończenia</th>\n'
        header += u'		</tr>\n'

        return(header)

    def PUtablefooter(self):
        footer = u'	</table>\n'

        return(footer)

        '''
        PDA Section
        '''

    def PDAheader(self):
        header = u'	<h2><a name="pdda"></a>Propozycje do Dobrych Artykułów</h2>\n'
        header += u'	<div class="detail"><a href="//pl.wikipedia.org/wiki/Plik:Information_icon.svg" class="image" title="Information icon.svg"><img alt="" src="//upload.wikimedia.org/wikipedia/commons/thumb/3/35/Information_icon.svg/15px-Information_icon.svg.png" border="0" height="15" width="15"></a> <i>Zobacz więcej na osobnej stronie: <a href="//pl.wikipedia.org/wiki/Wikipedia%3APropozycje%20do%20Dobrych%20Artyku%C5%82%C3%B3w" title="Wikipedia:Propozycje do Dobrych Artykułów">Wikipedia:Propozycje do Dobrych Artykułów</a>.</i></div>\n'

        return(header)

    def PDAtableheader(self):
	header = u'<table class="wikitable">\n'
        header += u'		<tr>\n'
        header += u'			<th>strona</th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:FlaggedRevs-2-1.svg" class="image" title="Liczba osób sprawdzających"><img alt="FlaggedRevs-2-1.svg" src="//upload.wikimedia.org/wikipedia/commons/thumb/5/52/FlaggedRevs-2-1.svg/18px-FlaggedRevs-2-1.svg.png" width="18" height="18"></a></th>\n'
        header += u'			<th>data zakończenia</th>\n'
        header += u'		</tr>\n'

        return(header)

    def PDAtablefooter(self):
        footer = u'	</table>\n'

        return(footer)

    '''
    PAM section
    '''

    def PAMheader(self):
        header = u'	<h2><a name="panm"></a>Propozycje do Artykułów na medal</h2>\n'
        header += u'	<div class="detail"><a href="//pl.wikipedia.org/wiki/Plik:Information_icon.svg" class="image" title="Information icon.svg"><img alt="" src="//upload.wikimedia.org/wikipedia/commons/thumb/3/35/Information_icon.svg/15px-Information_icon.svg.png" border="0" height="15" width="15"></a> <i>Zobacz więcej na osobnej stronie: <a href="//pl.wikipedia.org/wiki/Wikipedia%3APropozycje%20do%20Artyku%C5%82%C3%B3w%20na%20medal" title="Wikipedia:Propozycje do Artykułów na medal">Wikipedia:Propozycje do Artykułów na medal</a>.</i></div>\n'

        return(header)

    def PAMtableheader(self):
	header = u'<table class="wikitable">\n'
        header += u'		<tr>\n'
        header += u'			<th>strona</th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:FlaggedRevs-2-1.svg" class="image" title="Liczba osób sprawdzających"><img alt="FlaggedRevs-2-1.svg" src="//upload.wikimedia.org/wikipedia/commons/thumb/5/52/FlaggedRevs-2-1.svg/18px-FlaggedRevs-2-1.svg.png" width="18" height="18"></a></th>\n'
        header += u'			<th>data zakończenia</th>\n'
        header += u'		</tr>\n'

        return(header)

    def PAMtablefooter(self):
        footer = u'	</table>\n'

        return(footer)

    '''
    INM section
    '''
    def INMheader(self):
        header = u'	<h2><a name="gnm"></a>Ilustracja na medal</h2>\n'
        header += u'	<div class="detail"><a href="//pl.wikipedia.org/wiki/Plik:Information_icon.svg" class="image" title="Information icon.svg"><img alt="" src="//upload.wikimedia.org/wikipedia/commons/thumb/3/35/Information_icon.svg/15px-Information_icon.svg.png" border="0" height="15" width="15"></a> <i>Zobacz więcej na osobnej stronie: <a href="//pl.wikipedia.org/wiki/Wikipedia%3AIlustracja%20na%20medal%20-%20propozycje" title="Wikipedia:Ilustracja na medal - propozycje">Wikipedia:Ilustracja na medal - propozycje</a>.</i></div>\n'

        return(header)

    def INMtableheader(self):
	header = u'<table class="wikitable">\n'
        header += u'		<tr>\n'
        header += u'			<th>strona</th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:Symbol_support_vote.svg" class="image" title="Liczba głosów za"><img alt="+" src="//upload.wikimedia.org/wikipedia/commons/thumb/9/94/Symbol_support_vote.svg/15px-Symbol_support_vote.svg.png" border="0" height="15" width="15"></a></th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:Symbol_oppose_vote.svg" class="image" title="Liczba głosów przeciw"><img alt="-" src="//upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Symbol_oppose_vote.svg/15px-Symbol_oppose_vote.svg.png" border="0" height="15" width="15"></a></th>\n'
        header += u'			<th>netto</th>\n'
        header += u'			<th>%</th>\n'
        header += u'			<th>data zakończenia</th>\n'
        header += u'		</tr>'

        return(header)

    def INMtablefooter(self):
        footer = u'	</table>\n'

        return(footer)

    '''
    LNM section
    '''
    def LNMheader(self):
        header = u'	<h2><a name="plnm"></a>Propozycje do List na medal</h2>\n'
        header += u'	<div class="detail"><a href="//pl.wikipedia.org/wiki/Plik:Information_icon.svg" class="image" title="Information icon.svg"><img alt="" src="//upload.wikimedia.org/wikipedia/commons/thumb/3/35/Information_icon.svg/15px-Information_icon.svg.png" border="0" height="15" width="15"></a> <i>Zobacz więcej na osobnej stronie: <a href="//pl.wikipedia.org/wiki/Wikipedia%3APropozycje%20do%20List%20na%20medal" title="Wikipedia:Propozycje do List na medal">Wikipedia:Propozycje do List na medal</a>.</i></div>\n'

        return(header)

    def LNMtableheader(self):
	header = u'<table class="wikitable">\n'
        header += u'		<tr>\n'
        header += u'			<th>strona</th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:Symbol_support_vote.svg" class="image" title="Liczba głosów za"><img alt="+" src="//upload.wikimedia.org/wikipedia/commons/thumb/9/94/Symbol_support_vote.svg/15px-Symbol_support_vote.svg.png" border="0" height="15" width="15"></a></th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:Symbol_oppose_vote.svg" class="image" title="Liczba głosów przeciw"><img alt="-" src="//upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Symbol_oppose_vote.svg/15px-Symbol_oppose_vote.svg.png" border="0" height="15" width="15"></a></th>\n'
        header += u'			<th>netto</th>\n'
        header += u'			<th>%</th>\n'
        header += u'			<th>data zakończenia</th>\n'
        header += u'		</tr>'

        return(header)

    def LNMtablefooter(self):
        footer = u'	</table>\n'

        return(footer)

    '''
    PDGA section
    '''
    def PDGAheader(self):
        header = u'	<h2><a name="plnm"></a>Propozycje do Grup Artykułów</h2>\n'
        header += u'	<div class="detail"><a href="//pl.wikipedia.org/wiki/Plik:Information_icon.svg" class="image" title="Information icon.svg"><img alt="" src="//upload.wikimedia.org/wikipedia/commons/thumb/3/35/Information_icon.svg/15px-Information_icon.svg.png" border="0" height="15" width="15"></a> <i>Zobacz więcej na osobnej stronie: <a href="//pl.wikipedia.org/wiki/Wikipedia%3APropozycje%20do%20Grup%20Artyku%C5%82%C3%B3w" title="Wikipedia:Propozycje do Grup Artykułów">Wikipedia:Propozycje do Grup Artykułów</a>.</i></div>\n'

        return(header)

    def PDGAtableheader(self):
	header = u'<table class="wikitable">\n'
        header += u'		<tr>\n'
        header += u'			<th>strona</th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:Symbol_support_vote.svg" class="image" title="Liczba głosów za"><img alt="+" src="//upload.wikimedia.org/wikipedia/commons/thumb/9/94/Symbol_support_vote.svg/15px-Symbol_support_vote.svg.png" border="0" height="15" width="15"></a></th>\n'
        header += u'			<th><a href="//pl.wikipedia.org/wiki/Plik:Symbol_oppose_vote.svg" class="image" title="Liczba głosów przeciw"><img alt="-" src="//upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Symbol_oppose_vote.svg/15px-Symbol_oppose_vote.svg.png" border="0" height="15" width="15"></a></th>\n'
        header += u'			<th>netto</th>\n'
        header += u'			<th>%</th>\n'
        header += u'			<th>data zakończenia</th>\n'
        header += u'		</tr>'

        return(header)

    def PDGAtablefooter(self):
        footer = u'	</table>\n'

        return(footer)

    def ranklist(self,sortedlist):
        """
        Return list of ranks in results
        """

        result = []
        counter = 1
        rank = 1
        previousnetto = 0

        for p in sortedlist:
            wiki,error,z,p,n,netto,percent = p
            if self.getOption('test'):
                pywikibot.output(u'Name:%s votes:%s, previous:%s, count:%s' % (wiki,netto, previousnetto, counter))
            if counter == 1:
                previousnetto = netto
            else:
                if netto == previousnetto:
                    if self.getOption('test'):
                        pywikibot.output(u'Tied')
                    pass
                else:
                    rank = counter
                    previousnetto = netto
            if self.getOption('test'):
                pywikibot.output(u'Rank:%s' % rank)
            result.append(rank)
            counter += 1
        if self.getOption('test'):
            pywikibot.output(u'Ranks:%s' % result)

        return(result)


    def generateresultspage(self, results):
        """
        Generates results page from redirlist
        Starting with header, ending with footer
        Output page is pagename
        """
        #pywikibot.output(u'****Generate Results Page****')

        output = self.mainheader()
        sortablelist = []

        
        # KA section
        if self.getOption('KA'):
            output += self.KAheader()
            if 'KA' in results.keys():
                output += self.KAtableheader()

                #sorted list
                pywikibot.output(results['KA'])
                for p in results['KA']:
                    if not p == None:
                        (wiki,error, counters) = p
                        if not error:
                            (z,p,n,netto,percent) = counters
                            sortablelist.append( (wiki,error,z,p,n,netto,percent) )
                        else:
                            sortablelist.append( (wiki,error,-9999,-9999,-9999,-9999,0) )

                sortedVotes = sorted(sortablelist, key=lambda tup: tup[5], reverse=True)
                if self.getOption('test'):
                    pywikibot.output(u'SORTEDVOTES:')
                    pywikibot.output(sortedVotes)

                ranks = self.ranklist(sortedVotes)
                lastrank = ranks[int(self.getOption('KAplaces'))-1]
                if self.getOption('test'):
                    pywikibot.output(u'Last rank:%i' % lastrank)

                # with sorting
                rowscount = 0
                for p in sortedVotes:
                    (wiki,error, z,p,n,netto,percent) = p
                    if not error:
                        if netto >= 0:
                            if ranks[rowscount] == lastrank:
                                output += u'	<tr class="tied">\n'
                            elif rowscount < int(self.getOption('KAplaces')):
                                output += u'	<tr class="valid">\n'
                            else:
                                output += u'	<tr>\n'
                        else:
                            output += u'	<tr>\n'
                        
                        #output += u'	<tr>\n'
                        output += u'		<td><center>' + str(ranks[rowscount]) + u'.</center></td>'
                        link = urllib.quote((u'//pl.wikipedia.org/wiki/Wikipedia:Komitet_Arbitrażowy/Wybór_członków/' + self.getOption('KAmonth') + u'/' + wiki).encode('utf-8'))
                        output += u'		<td><center><a href="' + link + u'">' + wiki + u'</a></center></td>'
                        output += u'		<td>' + str(z) + u'</td>'
                        output += u'		<td>' + str(p) + u'</td>'
                        output += u'		<td>' + str(n) + u'</td>'
                        output += u'		<td><b>' + str(netto) + u'</b></td>'
                        output += u'		<td>' + "{0:.2f}".format((percent*1000)/10.0) + u'</td>'
                    else:
                        output += u'	<tr class="invalid">\n'
                        output += u'		<td colspan="6">nie można odczytać danych</td>\n'
                    output += u'	</tr>\n'
                    rowscount += 1
                output += self.KAtablefooter()
            else:
                output += u'\n<p>Aktualnie brak trwających głosowań.</p>\n'
        

        # PU section
        output += self.PUheader()
        if 'PU' in results.keys():
            output += self.PUtableheader()
            for p in results['PU']:
                (wiki,error, counters) = p
                output += u'	<tr>\n'
                link = urllib.quote((u'//pl.wikipedia.org/wiki/Wikipedia:Przyznawanie uprawnień/' + wiki).encode('utf-8'))
                output += u'		<td><a href="' + link + u'">' + wiki + u'</a></td>'
                if not error:
                    (z,p,n,netto,percent,date) = counters
                    output += u'		<td>' + str(z) + u'</td>'
                    output += u'		<td>' + str(p) + u'</td>'
                    output += u'		<td>' + str(n) + u'</td>'
                    output += u'		<td>' + str(netto) + u'</td>'
                    output += u'		<td>' + "{0:.2f}".format((percent*1000)/10.0) + u'</td>'
                    output += u'		<td>' + date + u'</td>\n' 
                else:
                    output += u'		<td colspan="6" style="color:red">nie można odczytać danych</td>\n'
                output += u'	</tr>\n'
            output += self.PUtablefooter()
        else:
            output += u'\n<p>Aktualnie brak trwających głosowań.</p>\n'


        # PDA section
        output += self.PDAheader()
        if 'PDA' in results.keys():
            output += self.PDAtableheader()
            for p in results['PDA']:
                (wiki, error, counters) = p
                output += u'	<tr>\n'
                link = urllib.quote((u'//pl.wikipedia.org/wiki/Wikipedia:Propozycje do Dobrych Artykułów/' + wiki).encode('utf-8'))
                output += u'		<td><a href="' + link + u'">' + wiki + u'</a></td>'
                if not error:
                    (v, date) = counters
                    output += u'		<td>' + str(v) + u'</td>'
                    output += u'		<td>' + date + u'</td>\n' 
                else:
                    output += u'		<td colspan="2" style="color:red">nie można odczytać danych</td>\n'
                output += u'	</tr>\n'

            output += self.PDAtablefooter()
        else:
            output += u'\n<p>Aktualnie brak trwających głosowań.</p>\n'

        # PAM section
        output += self.PAMheader()
        if 'PAM' in results.keys():
            output += self.PAMtableheader()
            for p in results['PAM']:
                (wiki,error, counters) = p
                output += u'	<tr>\n'
                link = urllib.quote((u'//pl.wikipedia.org/wiki/Wikipedia:Propozycje do Artykułów na medal/' + wiki).encode('utf-8'))
                output += u'		<td><a href="' + link + u'">' + wiki + u'</a></td>'
                if not error:
                    (v, date) = counters
                    output += u'		<td>' + str(v) + u'</td>'
                    output += u'		<td>' + date + u'</td>\n' 
                else:
                    output += u'		<td colspan="2" style="color:red">nie można odczytać danych</td>\n'
                output += u'	</tr>\n'
            output += self.PAMtablefooter()
        else:
            output += u'\n<p>Aktualnie brak trwających głosowań.</p>\n'

        # INM section
        output += self.INMheader()
        if 'INM' in results.keys():
            output += self.INMtableheader()
            for p in results['INM']:
                (wiki, error, counters) = p
                output += u'	<tr>\n'
                link = urllib.quote((u'//pl.wikipedia.org/wiki/Wikipedia:Ilustracja na medal - propozycje/' + wiki).encode('utf-8'))
                output += u'		<td><a href="' + link + u'">' + wiki + u'</a></td>'
                if not error:
                    (z,p,netto,percent,date) = counters
                    output += u'		<td>' + str(z) + u'</td>'
                    output += u'		<td>' + str(p) + u'</td>'
                    output += u'		<td>' + str(netto) + u'</td>'
                    output += u'		<td>' + "{0:.2f}".format((percent*1000)/10.0) + u'</td>'
                    output += u'		<td>' + date + u'</td>\n' 
                else:
                    output += u'		<td colspan="5" style="color:red">nie można odczytać danych</td>\n'
                output += u'	</tr>\n'

            output += self.INMtablefooter()
        else:
            output += u'\n<p>Aktualnie brak trwających głosowań.</p>\n'

        
        # LNM section
        output += self.LNMheader()
        if 'LNM' in results.keys():
            output += self.LNMtableheader()
            for p in results['LNM']:
                (wiki, error, counters) = p
                output += u'	<tr>\n'
                link = urllib.quote((u'//pl.wikipedia.org/wiki/Wikipedia:Propozycje_do_List_na_medal/' + wiki).encode('utf-8'))
                output += u'		<td><a href="' + link + u'">' + wiki + u'</a></td>'
                if not error:
                    (z,p,netto,percent,date) = counters
                    output += u'		<td>' + str(z) + u'</td>'
                    output += u'		<td>' + str(p) + u'</td>'
                    output += u'		<td>' + str(netto) + u'</td>'
                    output += u'		<td>' + "{0:.2f}".format((percent*1000)/10.0) + u'</td>'
                    output += u'		<td>' + date + u'</td>\n' 
                else:
                    output += u'		<td colspan="5" style="color:red">nie można odczytać danych</td>\n'
                output += u'	</tr>\n'

            output += self.LNMtablefooter()
        else:
            output += u'\n<p>Aktualnie brak trwających głosowań.</p>\n'

        
        # PDGA section
        output += self.PDGAheader()
        if 'PDGA' in results.keys():
            output += self.PDGAtableheader()
            for p in results['PDGA']:
                (wiki, error, counters) = p
                output += u'	<tr>\n'
                link = urllib.quote((u'//pl.wikipedia.org/wiki/Wikipedia:Propozycje_do_Grup_Artykułów/' + wiki).encode('utf-8'))
                output += u'		<td><a href="' + link + u'">' + wiki + u'</a></td>'
                if not error:
                    (z,p,netto,percent,date) = counters
                    output += u'		<td>' + str(z) + u'</td>'
                    output += u'		<td>' + str(p) + u'</td>'
                    output += u'		<td>' + str(netto) + u'</td>'
                    output += u'		<td>' + "{0:.2f}".format((percent*1000)/10.0) + u'</td>'
                    output += u'		<td>' + date + u'</td>\n' 
                else:
                    output += u'		<td colspan="5" style="color:red">nie można odczytać danych</td>\n'
                output += u'	</tr>\n'

            output += self.PDGAtablefooter()
        else:
            output += u'\n<p>Aktualnie brak trwających głosowań.</p>\n'
            #output += u'\n<p>Statystyka w przygotowaniu</p>\n\n'
        

        # closing section
        output += self.mainfooter()

        # write ready file
        #test
        #pywikibot.output(u'Writing file: %s' % self.getOption('outpage'))
        rf= open(u'masti/html/'+self.getOption('outpage'),'w')
        rf.write(output.encode('utf8'))
        rf.close()
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
        if option in ('summary', 'text', 'outpage','KAmonth', 'KAplaces'):
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
