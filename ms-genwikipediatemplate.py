#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An incomplete sample script by masti for creating statistics/listings pages
This is not a complete bot; rather, it is a template from which simple
bots can be made. You can rename it to mybot.py, then edit it in
whatever way you want.
Use global -simulate option for test purposes. No changes to live wiki
will be done.
Call:
	python pwb.py masti/ms-contains.py -catr:"Posłowie do Knesetu" -outpage:"Wikipedysta:Andrzei111/Izrael/bez Kneset" \
		-summary:"Bot uaktualnia tabelę" -text:"{{Kneset" -negative
	python pwb.py masti/ms-contains.py -weblink:'isap.sejm.gov.pl' -outpage:"Wikipedysta:mastiBot/isap" \
		-summary:"Bot uaktualnia tabelę" -text:"http://isap\.sejm\.gov\.pl/Download\?id=WD[^\s\]\|]*" -ns:0 -regex
	python pwb.py masti/ms-contains.py -weblink:'isap.sejm.gov.pl' -outpage:"Wikipedysta:mastiBot/isap" \
		-summary:"Bot uaktualnia tabelę" -text:"(?P<result>http://isap\.sejm\.gov\.pl/Download\?id=WD[^\s\]\|]*)" -ns:0 -regex
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
-regex:           treat text as regex - should contain <result> group. if not whole match will be used
-multi:           return all results for -regex not only first match
-flags:           list of regex flags: i,m,g,s etc.
-edit:            link thru template:edytuj instead of wikilink
-cite:            cite search results
-nowiki:          put citation in <nowiki> tags
-navi:            add navigation template {{Wikipedysta:MastiBot/Nawigacja|Wikipedysta:mastiBot/test|Wikipedysta:mastiBot/test 2}}
-progress:        report progress
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
    MultipleSitesBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)
from pywikibot.tools import issue_deprecation_warning
import re
import urllib2
import datetime

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class BasicBot(
    # Refer pywikobot.bot for generic bot classes
    #SingleSiteBot,  # A bot only working on one site
    MultipleSitesBot,  # A bot working on multiple sites
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

    wikipedias = {
        'af' : '[[Afrykanerska Wikipedia|afrykanerska]]',
        'als' : '[[Edycje językowe Wikipedii#A|alemańska]]',
        'am' : '[[Edycje językowe Wikipedii#A|amharska]]',
        'an' : '[[Aragońska Wikipedia|aragońska]]',
        'ar' : '[[Arabskojęzyczna Wikipedia|arabska]]',
        'arz' : '[[Egipsko-arabska Wikipedia|egipsko-arabska]]',
        'ast' : '[[Edycje językowe Wikipedii#A|asturyjska]]',
        'az' : '[[Azerska Wikipedia|azerska]]',
        'azb' : '[[Edycje językowe Wikipedii#A|południowoazerska]]',
        'ba' : '[[Baszkirska Wikipedia|baszkirska]]',
        'bar' : '[[Edycje językowe Wikipedii#B|bawarska]]',
        'bat-smg' : '[[Żmudzka Wikipedia|żmudzka]]',
        'be-tarask' : '[[Wikipedia w języku białoruskim (taraszkiewicy)|białoruska (taraszkiewica)]]',
        'be' : '[[Białoruskojęzyczna Wikipedia|białoruska]]',
        'bg' : '[[Bułgarska Wikipedia|bułgarska]]',
        'bh' : '[[Edycje językowe Wikipedii#B|bihari]]',
        'bn' : '[[Bengalska Wikipedia|bengalska]]',
        'bpy' : '[[Wikipedia w języku bisznuprija-manipuri|bisznuprija-manipuri]]',
        'br' : '[[Bretońska Wikipedia|bretońska]]',
        'bs' : '[[Bośniacka Wikipedia|bośniacka]]',
        'bug' : '[[Wikipedia w języku bugijskim|bugijska]]',
        'ca' : '[[Katalońska Wikipedia|katalońska]]',
        'cdo' : '[[Edycje językowe Wikipedii#M|mindong]]',
        'ce' : '[[Czeczeńska Wikipedia|czeczeńska]]',
        'ceb' : '[[Wikipedia w języku cebuańskim|cebuańska]]',
        'ckb' : '[[Edycje językowe Wikipedii#S|sorańska]]',
        'cs' : '[[Czeska Wikipedia|czeska]]',
        'cv' : '[[Czuwaska Wikipedia|czuwaska]]',
        'cy' : '[[Walijska Wikipedia|walijska]]',
        'da' : '[[Duńska Wikipedia|duńska]]',
        'de' : '[[Niemieckojęzyczna Wikipedia|niemiecka]]',
        'el' : '[[Grecka Wikipedia|grecka]]',
        'eml' : '[[Edycje językowe Wikipedii#E|emilijski]]',
        'en' : '[[Anglojęzyczna Wikipedia|angielska]]',
        'eo' : '[[Wikipedia w języku esperanto|esperanto]]',
        'es' : '[[Hiszpańskojęzyczna Wikipedia|hiszpańska]]',
        'et' : '[[Estońska Wikipedia|estońska]]',
        'eu' : '[[Baskijska Wikipedia|baskijska]]',
        'fa' : '[[Perska Wikipedia|perska]]',
        'fi' : '[[Fińska Wikipedia|fińska]]',
        'fo' : '[[Farerska Wikipedia|farerska]]',
        'fr' : '[[Francuskojęzyczna Wikipedia|francuska]]',
        'fy' : '[[Zachodniofryzyjska Wikipedia|zachodniofryzyjska]]',
        'ga' : '[[Irlandzka Wikipedia|irlandzka]]',
        'gd' : '[[Szkocka Gaelicka Wikipedia|szkocka gaelicka]]',
        'gl' : '[[Galicyjska Wikipedia|galicyjska]]',
        'gu' : '[[Gudźaracka Wikipedia|gudźaracka]]',
        'he' : '[[Hebrajska Wikipedia|hebrajska]] ',
        'hi' : '[[Wikipedia w języku hindi|hindi]]',
        'hif' : '[[Edycje językowe Wikipedii#H|hindi fidżyjskie]]',
        'hr' : '[[Chorwacka Wikipedia|chorwacka]]',
        'hsb' : '[[Górnołużycka Wikipedia|górnołużycka]]',
        'ht' : '[[Haitańska Wikipedia|haitańska]]',
        'hu' : '[[Węgierska Wikipedia|węgierska]]',
        'hy' : '[[Ormiańska Wikipedia|ormiańska]]',
        'ia' : '[[Edycje językowe Wikipedii#I|interlingua]]',
        'id' : '[[Indonezyjska Wikipedia|indonezyjska]]',
        'ilo' : '[[Edycje językowe Wikipedii#I|ilokkańska]]',
        'io' : '[[Wikipedia w języku ido|ido]]',
        'is' : '[[Islandzka Wikipedia|islandzka]]',
        'it' : '[[Włoska Wikipedia|włoska]]',
        'ja' : '[[Japońska Wikipedia|japońska]]',
        'jv' : '[[Jawajska Wikipedia|jawajska]]',
        'ka' : '[[Gruzińska Wikipedia|gruzińska]]',
        'kk' : '[[Kazachska Wikipedia|kazachska]]',
        'kn' : '[[Wikipedia w języku kannada|kannada]]',
        'ko' : '[[Koreańska Wikipedia|koreańska]]',
        'ku' : '[[Kurdyjska Wikipedia|kurdyjska]]',
        'ky' : '[[Kirgiska Wikipedia|kirgiska]]',
        'la' : '[[Łacińska Wikipedia|łacińska]]',
        'lb' : '[[Edycje językowe Wikipedii#L|luksemburska]]',
        'li' : '[[Edycje językowe Wikipedii#L|limburska]]',
        'lmo' : '[[Lombardzka Wikipedia|lombardzka]]',
        'lt' : '[[Litewska Wikipedia|litewska]]',
        'lv' : '[[Łotewska Wikipedia|łotewska]]',
        'mai' : '[[Edycje językowe Wikipedii#M|maithili]]',
        'map-bms' : '[[Edycje językowe Wikipedii#B|banjumasańska]]',
        'mg' : '[[Edycje językowe Wikipedii#M|malagaska]]',
        'mhr' : '[[Edycje językowe Wikipedii#M|wschodni dialekt Mari]]',
        'min' : '[[Edycje językowe Wikipedii#M|minangkabau]]',
        'mk' : '[[Edycje językowe Wikipedii#M|macedońska]]',
        'ml' : '[[Wikipedia w języku malajalam|malajalam]]',
        'mn' : '[[Mongolska Wikipedia|mongolska]]',
        'mr' : '[[Wikipedia w języku marathi|marathi]]',
        'mrj' : '[[Edycje językowe Wikipedii#Z|zachodnio-maryjska]]',
        'ms' : '[[Malajska Wikipedia|malajska]]',
        'my' : '[[Edycje językowe Wikipedii#B|birmańska]]',
        'mzn' : '[[Edycje językowe Wikipedii#M|mazanderańska]]',
        'nap' : '[[Neapolitańska Wikipedia|neapolitańska]]',
        'nds' : '[[Dolnoniemiecka Wikipedia|dolnoniemiecka]]',
        'ne' : '[[Edycje językowe Wikipedii#N|nepalska]]',
        'new' : '[[Newarska Wikipedia|newarska]]',
        'nl' : '[[Niderlandzka Wikipedia|niderlandzka]]',
        'nn' : '[[Wikipedia w języku norweskim (nynorsk)|norweska (nynorsk)]]',
        'no' : '[[Norweska Wikipedia|norweska (bokmål)]]',
        'oc' : '[[Oksytańska Wikipedia|oksytańska (prowansalska)]]',
        'or' : '[[Wikipedia w języku orija|orija]]',
        'os' : '[[Osetyjska Wikipedia|osetyjska]]',
        'pa' : '[[Pendżabska Wikipedia|pendżabska]]',
        'pl' : '[[polskojęzyczna Wikipedia|polska]]',
        'pms' : '[[Piemoncka Wikipedia|piemoncka]]',
        'pnb' : '[[Zachodniopendżabska Wikipedia|zachodniopendżabska]]',
        'pt' : '[[Portugalskojęzyczna Wikipedia|portugalska]]',
        'qu' : '[[Wikipedia w języku keczua|keczua]]',
        'ro' : '[[Rumuńska Wikipedia|rumuńska]]',
        'roa-tara' : '[[Tarencka Wikipedia|tarencka]]',
        'ru' : '[[Rosyjskojęzyczna Wikipedia|rosyjska]]',
        'sa' : '[[Edycje językowe Wikipedii#S|w sanskrycie]]',
        'sah' : '[[Edycje językowe Wikipedii#J|jakucka]]',
        'scn' : '[[Sycylijska Wikipedia|sycylijska]]',
        'sco' : '[[Wikipedia w języku scots|szkocka]]',
        'sh' : '[[Serbsko-chorwacka Wikipedia|serbsko-chorwacka]]',
        'si' : '[[Edycje językowe Wikipedii#S|syngaleska]]',
        'simple' : '[[Wikipedia w języku Simple English|angielska uproszczona]]',
        'sk' : '[[Słowacka Wikipedia|słowacka]]',
        'sl' : '[[Słoweńska Wikipedia|słoweńska]]',
        'sq' : '[[Albańska Wikipedia|albańska]]',
        'sr' : '[[Serbska Wikipedia|serbska]]',
        'su' : '[[Sundajska Wikipedia|sundajska]]',
        'sv' : '[[Szwedzka Wikipedia|szwedzka]]',
        'sw' : '[[Suahilijska Wikipedia|suahilijska]]',
        'szl' : '[[Śląska Wikipedia|śląska]]',
        'ta' : '[[Tamilska Wikipedia|tamilska]]',
        'te' : '[[Wikipedia w języku telugu|telugu]]',
        'tg' : '[[Tadżycka Wikipedia|tadżycka]]',
        'th' : '[[Tajska Wikipedia|tajska]]',
        'tl' : '[[Wikipedia w języku tagalog|tagalska]]',
        'tr' : '[[Turecka Wikipedia|turecka]]',
        'tt' : '[[Tatarska Wikipedia|tatarska]]',
        'uk' : '[[Ukraińska Wikipedia|ukraińska]]',
        'ur' : '[[Wikipedia w języku urdu|urdu]]',
        'uz' : '[[Uzbecka Wikipedia|uzbecka]]',
        'vec' : '[[Wenecka Wikipedia|wenecka]]',
        'vi' : '[[Wietnamska Wikipedia|wietnamska]]',
        'vo' : '[[Wikipedia w języku volapük|volapük]]',
        'wa' : '[[Walońska Wikipedia|walońska]]',
        'war' : '[[Wikipedia w języku warajskim|warajska]]',
        'xmf' : '[[Edycje językowe Wikipedii#M|megrelska]]',
        'yi' : '[[Wikipedia w języku jidysz|jidysz]]',
        'yo' : '[[Edycje językowe Wikipedii#J|joruba]]',
        'yo' : '[[Wikipedia w języku joruba|joruba]]',
        'zh-min-nan' : '[[Minnańska Wikipedia|minnańska]]',
        'zh-yue' : '[[Kantońska Wikipedia|kantońska]]',
        'zh' : '[[Chińska Wikipedia|chińska]]',
    }


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
            'text': 'Test',  #default search string 'Test' is default
            'top': False,  # append text on top of the page
            'outpage': u'Wikipedysta:mastiBot/test', #default output page
            'maxlines': 1000, #default number of entries per page
            'negative': False, #if True mark pages that DO NOT contain search string
            'test': False, #switch on test functionality
            'regex': False, #use text as regex
            'aslink': False, #put links as wikilinks
            'append': False, #append results to page
            'section': None, #section title
            'title': False, #check in title not text
            'multi': False, #'^' and '$' will now match begin and end of each line.
            'flags': None, #list of regex flags
            'edit': False, #link thru template:edytuj instead of wikilink
            'cite': False, #cite search results
            'nowiki': False, #put citation in <nowiki> tags
            'count': False, #count pages only
            'navi': False, # add navigation template
            'progress': False, # report progress
        })

        # call constructor of the super class
        super(BasicBot, self).__init__(**kwargs)

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
        
        reflinks = {} #initiate dict lang:size
        pagecounter = 0
        duplicates = 0
        marked = 0

        metasite = pywikibot.Site('meta','meta')
        metapage = pywikibot.Page(metasite,'List of Wikipedias/Table')

        if self.getOption('test'):
            pywikibot.output(u'[%s] Treating: %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),metapage.title(asLink=True,forceInterwiki=True)))

        refs = self.treat(metapage) 

        outputpage = self.getOption('outpage')

        result = self.generateresultspage(refs,outputpage)
        
        return

    def datepl(self):
        #return string for pl date
        months = ['stycznia','lutego','marca','kwietnia','maja','czerwca','lipca','sierpnia','wrzesnia','października','listopada','grudnia']
        return(re.sub(ur' \d* ',' '+months[int(datetime.datetime.now().strftime("%m"))-1]+' ',datetime.datetime.now().strftime("%-d %m %Y")))

    def assemblepage(self,artslists):
        # generate final page
        sections = ['5 000 000+', '2 000 000+', '1 000 000+', '500 000+', '200 000+', '100 000+', '50 000+', '25 000+', '10 000+' ]


        #finalpage = header
        finalpage = u'{{Navbox'
        finalpage += u'\n| nazwa = Wikipedie'
        finalpage += u'\n| tytuł = Edycje językowe [[Wikipedia|Wikipedii]] według liczby artykułów <small>(stan na %s)</small>' % self.datepl()

        i = 0
        while i<len(artslists):
            if self.getOption('test'):
                pywikibot.output(sections[i])
            finalpage += '\n\n| opis%i = %s' % (i+1, sections[i])
            finalpage += '\n| spis%i = ' % (i+1)
            first = True
            for a in artslists[i]:
                if self.getOption('test'):
                    pywikibot.output(a)
                if first:
                    first = False
                else:
                    finalpage += ' • '
                finalpage += a
            i += 1

        finalpage += u'\n\n| kategoria = '
        finalpage += u'\n}}'

        return(finalpage)                


    def generateresultspage(self, redirlist, pagename):
        """
        Generates results page from redirlist
        Output page is pagename
        """

        limits = [ 5000000, 2000000, 1000000, 500000, 200000, 100000, 50000, 25000, 10000 ]
        artlists = {0:[],1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[]}

        #pywikibot.output(finalpage)

        res = sorted(redirlist, key=redirlist.__getitem__, reverse=True)
        if self.getOption('test'):
            pywikibot.output(res)

        section = 0
        for w in res:
            #pywikibot.output('w:%s:%i' % (self.wikipedias[w],redirlist[w]))
            if redirlist[w] < limits[section]:
                section +=1
            if section > 8:
                break
            artlists[section].append('%s ([[:%s:]])' % (self.wikipedias[w],w))
        
        if self.getOption('test'):
            pywikibot.output(artlists)

        #pywikibot.output(self.assemblepage(artlists))

        #save results
        if self.getOption('test'):
            pywikibot.output(u'***** saving results *****')
        outpage = pywikibot.Page(pywikibot.Site(), self.getOption('outpage'))
        outpage.text = self.assemblepage(artlists)

        if self.getOption('test'):
            pywikibot.output(outpage.title())
        
        success = outpage.save(summary=self.getOption('summary'))

        return()
 
    def treat(self, page):
        """
        Returns dict of Wikipedia sizes lang:size
        """
        text = page.text
        wikiR = re.compile(ur"(?s)\| \[\[:(?P<lang>[\w-]*):.*?'''(?P<size>[\d,]*)")

        result = {}
        unknownwiki = []
        count = 1
        for w in wikiR.finditer(text):
            lang = w.group('lang')
            size = int(re.sub(ur',','',w.group('size')))
            if lang in self.wikipedias.keys():
                wiki = self.wikipedias[lang]
            else:
                wiki = '[**********]'
                unknownwiki.append(lang)
            result[lang] = size
            if self.getOption('test'):
                pywikibot.output(u'[%s][%i]L:%s W:%s S:%i' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), count, lang, wiki, size ))
            count += 1
        if self.getOption('test'):
            pywikibot.output(unknownwiki)
            pywikibot.output('Wikipedias:%i' % count)
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
        if option in ('summary', 'text', 'outpage', 'maxlines', 'section','flags'):
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
