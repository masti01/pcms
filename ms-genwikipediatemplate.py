#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Bot tu update {{Wikipedie}} on pl.wiki

Use global -simulate option for test purposes. No changes to live wiki
will be done.
Call:
    python pwb.py masti/ms-genwikipediatemplate.py -page:'Szablon:Wikipedie' -outpage:'Szablon:Wikipedie' -summary:'Bot uakktualnia stronę' -pt:0 -cosmeticchanges:No

The following parameters are supported:
&params;
-always           If used, the bot won't ask if it should file the message
                  onto user talk page.   
-outpage          Results page; otherwise "Wikipedysta:mastiBot/test" is used
-summary:         Set the action summary message for the edit.
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
        'aa':['[[Afarska Wikipedia|afarska]]', '[[Afarska Wikipedia|afarska]]'],
        'ab':['[[Abchaska Wikipedia|abchaska]]', '[[Abchaska Wikipedia|abchaska]]'],
        'ace':['[[Wikipedia w języku aceh|aceh]]', '[[Wikipedia w języku aceh|aceh]]'],
        'ady':['[[Adygejska Wikipedia|agedyjska]]', '[[Adygejska Wikipedia|agedyjska]]'],
        'af':['[[Afrykanerska Wikipedia|afrykanerska]]', '[[Afrykanerska Wikipedia|afrykanerska]]'],
        'ak':['[[Akańska Wikipedia|akańska]]', '[[Akańska Wikipedia|akańska]]'],
        'als':['[[Edycje językowe Wikipedii#A|alemańska]]', '[[Alemańska Wikipedia|alemańska]]'],
        'am':['[[Edycje językowe Wikipedii#A|amharska]]', '[[Amharska Wikipedia|amharska]]'],
        'an':['[[Aragońska Wikipedia|aragońska]]', '[[Aragońska Wikipedia|aragońska]]'],
        'ang':['[[Staroangielska Wikipedia|staroangielska]]', '[[Staroangielska Wikipedia|staroangielska]]'],
        'ar':['[[Arabskojęzyczna Wikipedia|arabska]]', '[[Arabskojęzyczna Wikipedia|arabska]]'],
        'arc':['[[Aramejska Wikipedia|aramejska]]', '[[Aramejska Wikipedia|aramejska]]'],
        'arz':['[[Edycje językowe Wikipedii#E|egipsko-arabska]]', '[[Egipsko-arabska Wikipedia|egipsko-arabska]]'],
        'as':['[[Edycje językowe Wikipedii#A|asamska]]', '[[Asamska Wikipedia|asamska]]'],
        'ast':['[[Edycje językowe Wikipedii#A|asturyjska]]', '[[Asturyjska Wikipedia|asturyjska]]'],
        'atj':['[[Atikamekwańska Wikipedia|atikamekwańska]]', '[[Atikamekwańska Wikipedia|atikamekwańska]]'],
        'av':['[[Awarska Wikipedia|awarska]]', '[[Awarska Wikipedia|awarska]]'],
        'ay':['[[Ajmarska Wikipedia|ajmarska]]', '[[Ajmarska Wikipedia|ajmarska]]'],
        'az':['[[Azerska Wikipedia|azerska]]', '[[Azerska Wikipedia|azerska]]'],
        'azb':['[[Południowoazerska Wikipedia|południowoazerska]]', '[[Południowoazerska Wikipedia|południowoazerska]]'],
        'ba':['[[Baszkirska Wikipedia|baszkirska]]', '[[Baszkirska Wikipedia|baszkirska]]'],
        'bar':['[[Bawarska Wikipedia|bawarska]]', '[[Bawarska Wikipedia|bawarska]]'],
        'bat-smg':['[[Żmudzka Wikipedia|żmudzka]]', '[[Żmudzka Wikipedia|żmudzka]]'],
        'bcl':['[[Bikolska Wikipedia|bikolska]]', '[[Bikolska Wikipedia|bikolska]]'],
        'be':['[[Białoruskojęzyczna Wikipedia|białoruska]]', '[[Białoruskojęzyczna Wikipedia|białoruska]]'],
        'be-tarask':['[[Wikipedia w języku białoruskim (taraszkiewicy)|białoruska (taraszkiewica)]]', '[[Wikipedia w języku białoruskim (taraszkiewicy)|białoruska (taraszkiewica)]]'],
        'bg':['[[Bułgarska Wikipedia|bułgarska]]', '[[Bułgarska Wikipedia|bułgarska]]'],
        'bh':['[[Wikipedia w języku bihari|bihari]]', '[[Wikipedia w języku bihari|bihari]]'],
        'bi':['[[Bislamska Wikipedia|bislamska]]', '[[Bislamska Wikipedia|bislamska]]'],
        'bjn':['[[Banjarska Wikipedia|banjarska]]', '[[Banjarska Wikipedia|banjarska]]'],
        'bm':['[[Bambaryjska Wikipedia|bamabryjska]]', '[[Bambaryjska Wikipedia|bamabryjska]]'],
        'bn':['[[Bengalska Wikipedia|bengalska]]', '[[Bengalska Wikipedia|bengalska]]'],
        'bo':['[[Edycje językowe Wikipedii#T|tybetańska]]', '[[Tybetańska Wikipedia|tybetańska]]'],
        'bpy':['[[Wikipedia w języku bisznuprija-manipuri|bisznuprija-manipuri]]', '[[Wikipedia w języku bisznuprija-manipuri|bisznuprija-manipuri]]'],
        'br':['[[Bretońska Wikipedia|bretońska]]', '[[Bretońska Wikipedia|bretońska]]'],
        'bs':['[[Bośniacka Wikipedia|bośniacka]]', '[[Bośniacka Wikipedia|bośniacka]]'],
        'bug':['[[Wikipedia w języku bugijskim|bugijska]]', '[[Wikipedia w języku bugijskim|bugijska]]'],
        'bxr':['[[Buriacka Wikipedia|buriacka]]', '[[Buriacka Wikipedia|buriacka]]'],
        'ca':['[[Katalońska Wikipedia|katalońska]]', '[[Katalońska Wikipedia|katalońska]]'],
        'cbk-zam':['[[Chavacańska Wikipedia|chavacańska]]', '[[Chavacańska Wikipedia|chavacańska]]'],
        'cdo':['[[Wikipedia w języku mindong|mindong]]', '[[Wikipedia w języku mindong|mindong]]'],
        'ce':['[[Czeczeńska Wikipedia|czeczeńska]]', '[[Czeczeńska Wikipedia|czeczeńska]]'],
        'ceb':['[[Wikipedia w języku cebuańskim|cebuańska]]', '[[Wikipedia w języku cebuańskim|cebuańska]]'],
        'ch':['[[Czamorryjska Wikipedia|czamorryjska]]', '[[Czamorryjska Wikipedia|czamorryjska]]'],
        'cho':['[[Czoktawska Wikipedia|czoktawska]]', '[[Czoktawska Wikipedia|czoktawska]]'],
        'chr':['[[Czirokeska Wikipedia|czirokeska]]', '[[Czirokeska Wikipedia|czirokeska]]'],
        'chy':['[[Czejeńska Wikipedia|czejeńska]]', '[[Czejeńska Wikipedia|czejeńska]]'],
        'ckb':['[[Edycje językowe Wikipedii#S|sorańska]]', '[[Sorańska Wikipedia|sorańska]]'],
        'co':['[[Edycje językowe Wikipedii#K|korsykańska]]', '[[Korsykańska Wikipedia|korsykańska]]'],
        'cr':['[[Wikipedia w języku kri|kri]]', '[[Wikipedia w języku kri|kri]]'],
        'crh':['[[Edycje językowe Wikipedii#K|krymskotatarska]]', '[[Krymskotatarska Wikipedia|krymskotatarska]]'],
        'cs':['[[Czeska Wikipedia|czeska]]', '[[Czeska Wikipedia|czeska]]'],
        'csb':['[[Kaszubska Wikipedia|kaszubska]]', '[[Kaszubska Wikipedia|kaszubska]]'],
        'cu':['[[Cerkiewnosłowiańska Wikipedia|cerkiewnosłowiańska]]', '[[Cerkiewnosłowiańska Wikipedia|cerkiewnosłowiańska]]'],
        'cv':['[[Czuwaska Wikipedia|czuwaska]]', '[[Czuwaska Wikipedia|czuwaska]]'],
        'cy':['[[Walijska Wikipedia|walijska]]', '[[Walijska Wikipedia|walijska]]'],
        'da':['[[Duńska Wikipedia|duńska]]', '[[Duńska Wikipedia|duńska]]'],
        'de':['[[Niemieckojęzyczna Wikipedia|niemiecka]]', '[[Niemieckojęzyczna Wikipedia|niemiecka]]'],
        'din':['[[Dinkańska Wikipedia|dinkańska]]', '[[Dinkańska Wikipedia|dinkańska]]'],
        'diq':['[[Zazakiańska Wikipedia|zazakiańska]]', '[[Zazakiańska Wikipedia|zazakiańska]]'],
        'dsb':['[[Edycje językowe Wikipedii#D|dolnołużycka]]', '[[Dolnołużycka Wikipedia|dolnołużycka]]'],
        'dty':['[[Wikipedia w języku doteli|doteli]]', '[[Wikipedia w języku doteli|doteli]]'],
        'dv':['[[Edycje językowe Wikipedii#M|malediwska]]', '[[Malediwska Wikipedia|malediwska]]'],
        'dz':['[[Dzongkhańska Wikipedia|dzongkhańska]]', '[[Dzongkhańska Wikipedia|dzongkhańska]]'],
        'ee':['[[Ewska Wikipedia|ewska]]', '[[Ewska Wikipedia|ewska]]'],
        'el':['[[Grecka Wikipedia|grecka]]', '[[Grecka Wikipedia|grecka]]'],
        'eml':['[[Emilijska Wikipedia|emilijska]]', '[[Emilijska Wikipedia|emilijska]]'],
        'en':['[[Anglojęzyczna Wikipedia|angielska]]', '[[Anglojęzyczna Wikipedia|angielska]]'],
        'eo':['[[Wikipedia w języku esperanto|esperanto]]', '[[Wikipedia w języku esperanto|esperanto]]'],
        'es':['[[Hiszpańskojęzyczna Wikipedia|hiszpańska]]', '[[Hiszpańskojęzyczna Wikipedia|hiszpańska]]'],
        'et':['[[Estońska Wikipedia|estońska]]', '[[Estońska Wikipedia|estońska]]'],
        'eu':['[[Baskijska Wikipedia|baskijska]]', '[[Baskijska Wikipedia|baskijska]]'],
        'ext':['[[Estremadurska Wikipedia|estremadurska]]', '[[Estremadurska Wikipedia|estremadurska]]'],
        'fa':['[[Perska Wikipedia|perska]]', '[[Perska Wikipedia|perska]]'],
        'ff':['[[Fulańska Wikipedia|fulańska]]', '[[Fulańska Wikipedia|fulańska]]'],
        'fi':['[[Fińska Wikipedia|fińska]]', '[[Fińska Wikipedia|fińska]]'],
        'fiu-vro':['[[Wikipedia w języku võro|võro]]', '[[Wikipedia w języku võro|võro]]'],
        'fj':['[[Fidżyjska Wikipedia|fidżyjska]]', '[[Fidżyjska Wikipedia|fidżyjska]]'],
        'fo':['[[Edycje językowe Wikipedii#F|farerska]]', '[[Farerska Wikipedia|farerska]]'],
        'fr':['[[Francuskojęzyczna Wikipedia|francuska]]', '[[Francuskojęzyczna Wikipedia|francuska]]'],
        'frp':['[[Franko-prowansalska Wikipedia|franko-prowansalska]]', '[[Franko-prowansalska Wikipedia|franko-prowansalska]]'],
        'frr':['[[Północnofryzyjska Wikipedia|północnofryzyjska]]', '[[Północnofryzyjska Wikipedia|północnofryzyjska]]'],
        'fur':['[[Edycje językowe Wikipedii#F|friulska]]', '[[Friulska Wikipedia|friulska]]'],
        'fy':['[[Zachodniofryzyjska Wikipedia|zachodniofryzyjska]]', '[[Zachodniofryzyjska Wikipedia|zachodniofryzyjska]]'],
        'ga':['[[Irlandzka Wikipedia|irlandzka]]', '[[Irlandzka Wikipedia|irlandzka]]'],
        'gag':['[[Gagauska Wikipedia|gagauska]]', '[[Gagauska Wikipedia|gagauska]]'],
        'gan':['[[Wikipedia w języku gan|gan]]', '[[Wikipedia w języku gan|gan]]'],
        'gd':['[[Szkocka Gaelicka Wikipedia|szkocka gaelicka]]', '[[Szkocka Gaelicka Wikipedia|szkocka gaelicka]]'],
        'gl':['[[Galicyjska Wikipedia|galicyjska]]', '[[Galicyjska Wikipedia|galicyjska]]'],
        'glk':['[[Giliańska Wikipedia|giliańska]]', '[[Giliańska Wikipedia|giliańska]]'],
        'gn':['[[Guarańska Wikipedia|guarańska]]', '[[Guarańska Wikipedia|guarańska]]'],
        'gom':['[[Konkańska Wikipedia|konkańska]]', '[[Konkańska Wikipedia|konkańska]]'],
        'got':['[[Gocka Wikipedia|gocka]]', '[[Gocka Wikipedia|gocka]]'],
        'gu':['[[Gudźaracka Wikipedia|gudźaracka]]', '[[Gudźaracka Wikipedia|gudźaracka]]'],
        'gv':['[[Maksjańska Wikipedia|maksjańska]]', '[[Maksjańska Wikipedia|maksjańska]]'],
        'ha':['[[Hausyjska Wikipedia|hausyjska]]', '[[Hausyjska Wikipedia|hausyjska]]'],
        'hak':['[[Wikipedia w języku hakka|hakka]]', '[[Wikipedia w języku hakka|hakka]]'],
        'haw':['[[Hawajska Wikipedia|hawajska]]', '[[Hawajska Wikipedia|hawajska]]'],
        'he':['[[Hebrajska Wikipedia|hebrajska ]]', '[[Hebrajska Wikipedia|hebrajska ]]'],
        'hi':['[[Wikipedia w języku hindi|hindi]]', '[[Wikipedia w języku hindi|hindi]]'],
        'hif':['[[Wikipedia w języku hindi fidżyjskim|hindi fidżyjskie]]', '[[Wikipedia w języku hindi fidżyjskie|hindi fidżyjskie]]'],
        'ho':['[[Wikipedia w języku hiri motu|hiri motu]]', '[[Wikipedia w języku hiri motu|hiri motu]]'],
        'hr':['[[Chorwacka Wikipedia|chorwacka]]', '[[Chorwacka Wikipedia|chorwacka]]'],
        'hsb':['[[Górnołużycka Wikipedia|górnołużycka]]', '[[Górnołużycka Wikipedia|górnołużycka]]'],
        'ht':['[[Haitańska Wikipedia|haitańska]]', '[[Haitańska Wikipedia|haitańska]]'],
        'hu':['[[Węgierska Wikipedia|węgierska]]', '[[Węgierska Wikipedia|węgierska]]'],
        'hy':['[[Ormiańska Wikipedia|ormiańska]]', '[[Ormiańska Wikipedia|ormiańska]]'],
        'hz':['[[Hererska Wikipedia|hererska]]', '[[Hererska Wikipedia|hererska]]'],
        'ia':['[[Edycje językowe Wikipedii#I|interlingua]]', '[[Wikipedia w języku interlingua|interlingua]]'],
        'id':['[[Indonezyjska Wikipedia|indonezyjska]]', '[[Indonezyjska Wikipedia|indonezyjska]]'],
        'ie':['[[Wikipedia w języku occidental|occidental]]', '[[Wikipedia w języku occidental|occidental]]'],
        'ig':['[[Wikipedia w języku igbo|igbo]]', '[[Wikipedia w języku igbo|igbo]]'],
        'ii':['[[Wikipedia w języku nuosu|nuosu]]', '[[Wikipedia w języku nuosu|nuosu]]'],
        'ik':['[[Wikipedia w języku inupiak|inupiak]]', '[[Wikipedia w języku inupiak|inupiak]]'],
        'ilo':['[[Ilokkańska Wikipedia|ilokkańska]]', '[[Ilokkańska Wikipedia|ilokkańska]]'],
        'io':['[[Wikipedia w języku ido|ido]]', '[[Wikipedia w języku ido|ido]]'],
        'is':['[[Islandzka Wikipedia|islandzka]]', '[[Islandzka Wikipedia|islandzka]]'],
        'it':['[[Włoska Wikipedia|włoska]]', '[[Włoska Wikipedia|włoska]]'],
        'iu':['[[Eskimoska Wikipedia|eskimoska]]', '[[Eskimoska Wikipedia|eskimoska]]'],
        'ja':['[[Japońska Wikipedia|japońska]]', '[[Japońska Wikipedia|japońska]]'],
        'jam':['[[Jamajska Wikipedia|jamajska]]', '[[Jamajska Wikipedia|jamajska]]'],
        'jbo':['[[Lojbańska Wikipedia|lojbańska]]', '[[Lojbańska Wikipedia|lojbańska]]'],
        'jv':['[[Jawajska Wikipedia|jawajska]]', '[[Jawajska Wikipedia|jawajska]]'],
        'ka':['[[Gruzińska Wikipedia|gruzińska]]', '[[Gruzińska Wikipedia|gruzińska]]'],
        'kaa':['[[Karakałpacka Wikipedia|karakałpacka]]', '[[Karakałpacka Wikipedia|karakałpacka]]'],
        'kab':['[[Kabylska Wikipedia|kabylska]]', '[[Kabylska Wikipedia|kabylska]]'],
        'kbd':['[[Kabardyjska Wikipedia|kabardyjska]]', '[[Kabardyjska Wikipedia|kabardyjska]]'],
        'kbp':['[[Wikipedia w języku kabiye|kabiye]]', '[[Wikipedia w języku kabiye|kabiye]]'],
        'kg':['[[Kongijska Wikipedia|kongijska]]', '[[Kongijska Wikipedia|kongijska]]'],
        'ki':['[[Kikujska Wikipedia|kikujska]]', '[[Kikujska Wikipedia|kikujska]]'],
        'kj':['[[Wikipedia w języku kwanyama|kwanyama]]', '[[Wikipedia w języku kwanyama|kwanyama]]'],
        'kk':['[[Kazachska Wikipedia|kazachska]]', '[[Kazachska Wikipedia|kazachska]]'],
        'kl':['[[Grenlandzka Wikipedia|grenlandzka]]', '[[Grenlandzka Wikipedia|grenlandzka]]'],
        'km':['[[Khmerska Wikipedia|khmerska]]', '[[Khmerska Wikipedia|khmerska]]'],
        'kn':['[[Wikipedia w języku kannada|kannada]]', '[[Wikipedia w języku kannada|kannada]]'],
        'ko':['[[Koreańska Wikipedia|koreańska]]', '[[Koreańska Wikipedia|koreańska]]'],
        'koi':['[[Komi-permiacka Wikipedia|komi-permiacka]]', '[[Komi-permiacka Wikipedia|komi-permiacka]]'],
        'kr':['[[Edycje językowe Wikipedii#K|kanurska]]', '[[Kanurska Wikipedia|kanurska]]'],
        'krc':['[[Karaczajsko-bałkarska Wikipedia|karaczajsko-bałkarska]]', '[[Karaczajsko-bałkarska Wikipedia|karaczajsko-bałkarska]]'],
        'ks':['[[Kaszmirska Wikipedia|kaszmirska]]', '[[Kaszmirska Wikipedia|kaszmirska]]'],
        'ksh':['[[Rypuaryjska Wikipedia|rypuaryjska]]', '[[Rypuaryjska Wikipedia|rypuaryjska]]'],
        'ku':['[[Edycje językowe Wikipedii#K|kurdyjska]]', '[[Kurdyjska Wikipedia|kurdyjska]]'],
        'kv':['[[Komska Wikipedia|komska]]', '[[Komska Wikipedia|komska]]'],
        'kw':['[[Edycje językowe Wikipedii#K|kornijska]]', '[[Kornijska Wikipedia|kornijska]]'],
        'ky':['[[Kirgiska Wikipedia|kirgiska]]', '[[Kirgiska Wikipedia|kirgiska]]'],
        'la':['[[Łacińska Wikipedia|łacińska]]', '[[Łacińska Wikipedia|łacińska]]'],
        'lad':['[[Edycje językowe Wikipedii#L|ladino]]', '[[Judeo-hiszpańska Wikipedia|ladino]]'],
        'lb':['[[Edycje językowe Wikipedii#L|luksemburska]]', '[[Luksemburska Wikipedia|luksemburska]]'],
        'lbe':['[[Lakijska Wikipedia|lakijska]]', '[[Lakijska Wikipedia|lakijska]]'],
        'lez':['[[Lezgińska Wikipedia|lezgińska]]', '[[Lezgińska Wikipedia|lezgińska]]'],
        'lg':['[[Lugandyjska Wikipedia|lugandyjska]]', '[[Lugandyjska Wikipedia|lugandyjska]]'],
        'li':['[[Edycje językowe Wikipedii#L|limburska]]', '[[Limburska Wikipedia|limburska]]'],
        'lij':['[[Liguryjska Wikipedia|liguryjska]]', '[[Liguryjska Wikipedia|liguryjska]]'],
        'lmo':['[[Lombardzka Wikipedia|lombardzka]]', '[[Lombardzka Wikipedia|lombardzka]]'],
        'ln':['[[Lingalska Wikipedia|lingalska]]', '[[Lingalska Wikipedia|lingalska]]'],
        'lo':['[[Laotańska Wikipedia|laotańska]]', '[[Laotańska Wikipedia|laotańska]]'],
        'lrc':['[[Luryjska Wikipedia|luryjska]]', '[[Luryjska Wikipedia|luryjska]]'],
        'lt':['[[Litewska Wikipedia|litewska]]', '[[Litewska Wikipedia|litewska]]'],
        'ltg':['[[Łatgalska Wikipedia|łatgalska]]', '[[Łatgalska Wikipedia|łatgalska]]'],
        'lv':['[[Łotewska Wikipedia|łotewska]]', '[[Łotewska Wikipedia|łotewska]]'],
        'mai':['[[Wikipedia w języku maithili|maithili]]', '[[Wikipedia w języku maithili|maithili]]'],
        'map-bms':['[[Banjumasańska Wikipedia|banjumasańska]]', '[[Banjumasańska Wikipedia|banjumasańska]]'],
        'mdf':['[[Mokszańska Wikipedia|mokszańska]]', '[[Mokszańska Wikipedia|mokszańska]]'],
        'mg':['[[Edycje językowe Wikipedii#M|malagaska]]', '[[Malagaska Wikipedia|malagaska]]'],
        'mh':['[[Marszalska Wikipedia|marszalska]]', '[[Marszalska Wikipedia|marszalska]]'],
        'mhr':['[[Edycje językowe Wikipedii#M|wschodni dialekt Mari]]', '[[Wikipedia we wschodnim dialekcie mari|wschodni dialekt Mari]]'],
        'mi':['[[Maoryska Wikipedia|maoryska]]', '[[Maoryska Wikipedia|maoryska]]'],
        'min':['[[Edycje językowe Wikipedii#M|minangkabau]]', '[[Wikipedia w języku minangkabau|minangkabau]]'],
        'mk':['[[Edycje językowe Wikipedii#M|macedońska]]', '[[Macedońska Wikipedia|macedońska]]'],
        'ml':['[[Wikipedia w języku malajalam|malajalam]]', '[[Wikipedia w języku malajalam|malajalam]]'],
        'mn':['[[Mongolska Wikipedia|mongolska]]', '[[Mongolska Wikipedia|mongolska]]'],
        'mr':['[[Edycje językowe Wikipedii#M|maracka]]', '[[Maracka Wikipedia|maracka]]'],
        'mrj':['[[Zachodniomaryjska Wikipedia|zachodniomaryjska]]', '[[Zachodniomaryjska Wikipedia|zachodniomaryjska]]'],
        'ms':['[[Malajska Wikipedia|malajska]]', '[[Malajska Wikipedia|malajska]]'],
        'mt':['[[Maltańska Wikipedia|maltańska]]', '[[Maltańska Wikipedia|maltańska]]'],
        'mus':['[[Kricka Wikipedia|kriacka]]', '[[Kricka Wikipedia|kriacka]]'],
        'mwl':['[[Mirandyjska Wikipedia|mirandyjska]]', '[[Mirandyjska Wikipedia|mirandyjska]]'],
        'my':['[[Birmańska Wikipedia|birmańska]]', '[[Birmańska Wikipedia|birmańska]]'],
        'myv':['[[Erzjańska Wikipedia|erzjańska]]', '[[Erzjańska Wikipedia|erzjańska]]'],
        'mzn':['[[Mazanderańska Wikipedia|mazanderańska]]', '[[Mazanderańska Wikipedia|mazanderańska]]'],
        'na':['[[Naurańska Wikipedia|naurańska]]', '[[Naurańska Wikipedia|naurańska]]'],
        'nah':['[[Wikipedia w języku nahuatl|nauhatl]]', '[[Wikipedia w języku nahuatl|nauhatl]]'],
        'nap':['[[Neapolitańska Wikipedia|neapolitańska]]', '[[Neapolitańska Wikipedia|neapolitańska]]'],
        'nds':['[[Dolnoniemiecka Wikipedia|dolnoniemiecka]]', '[[Dolnoniemiecka Wikipedia|dolnoniemiecka]]'],
        'nds-nl':['[[Dolnosaksońska Wikipedia|dolnosaksońska]]', '[[Dolnosaksońska Wikipedia|dolnosaksońska]]'],
        'ne':['[[Nepalska Wikipedia|nepalska]]', '[[Nepalska Wikipedia|nepalska]]'],
        'new':['[[Newarska Wikipedia|newarska]]', '[[Newarska Wikipedia|newarska]]'],
        'ng':['[[Wikipedia w języku ndonga|ndonga]]', '[[Wikipedia w języku ndonga|ndonga]]'],
        'nl':['[[Niderlandzka Wikipedia|niderlandzka]]', '[[Niderlandzka Wikipedia|niderlandzka]]'],
        'nn':['[[Wikipedia w języku norweskim (nynorsk)|norweska (nynorsk)]]', '[[Wikipedia w języku norweskim (nynorsk)|norweska (nynorsk)]]'],
        'no':['[[Norweska Wikipedia|norweska (bokmål)]]', '[[Norweska Wikipedia|norweska (bokmål)]]'],
        'nov':['[[Novialska Wikipedia|novialska]]', '[[Novialska Wikipedia|novialska]]'],
        'nrm':['[[Naromska Wikipedia|naromska]]', '[[Naromska Wikipedia|naromska]]'],
        'nso':['[[Wikipedia w języku północnym sotho|północny sotho]]', '[[Wikipedia w języku północnym sotho|północny sotho]]'],
        'nv':['[[Nawahska Wikipedia|nawahska]]', '[[Nawahska Wikipedia|nawahska]]'],
        'ny':['[[Cziczewska Wikipedia|cziczewska]]', '[[Cziczewska Wikipedia|cziczewska]]'],
        'oc':['[[Oksytańska Wikipedia|oksytańska (prowansalska)]]', '[[Oksytańska Wikipedia|oksytańska (prowansalska)]]'],
        'olo':['[[Karelska Wikipedia|karelska]]', '[[Karelska Wikipedia|karelska]]'],
        'om':['[[Wikipedia w języku oromo|oromo]]', '[[Wikipedia w języku oromo|oromo]]'],
        'or':['[[Wikipedia w języku orija|orija]]', '[[Wikipedia w języku orija|orija]]'],
        'os':['[[Osetyjska Wikipedia|osetyjska]]', '[[Osetyjska Wikipedia|osetyjska]]'],
        'pa':['[[Pendżabska Wikipedia|pendżabska]]', '[[Pendżabska Wikipedia|pendżabska]]'],
        'pag':['[[Wikipedia w języku pangasinan|pangasinan]]', '[[Wikipedia w języku pangasinan|pangasinan]]'],
        'pam':['[[Wikipedia w jezyku pampango|pampango]]', '[[Wikipedia w jezyku pampango|pampango]]'],
        'pap':['[[Papiamencka Wikipedia|papiamencka]]', '[[Papiamencka Wikipedia|papiamencka]]'],
        'pcd':['[[Pikardyjska Wikipedia|pikardyjska]]', '[[Pikardyjska Wikipedia|pikardyjska]]'],
        'pdc':['[[Pensylwańska Wikipedia|pensylwańska]]', '[[Pensylwańska Wikipedia|pensylwańska]]'],
        'pfl':['[[Palatynacka Wikipedia|palatynacka]]', '[[Palatynacka Wikipedia|palatynacka]]'],
        'pi':['[[Wikipedia w języku pali|pali]]', '[[Wikipedia w języku pali|pali]]'],
        'pih':['[[Pitkarnyjska Wikipedia|pitkarnyjska]]', '[[Pitkarnyjska Wikipedia|pitkarnyjska]]'],
        'pl':['[[Polskojęzyczna Wikipedia|polska]]', '[[Polskojęzyczna Wikipedia|polska]]'],
        'pms':['[[Piemoncka Wikipedia|piemoncka]]', '[[Piemoncka Wikipedia|piemoncka]]'],
        'pnb':['[[Zachodniopendżabska Wikipedia|zachodniopendżabska]]', '[[Zachodniopendżabska Wikipedia|zachodniopendżabska]]'],
        'pnt':['[[Pontyjska Wikipedia|pontyjska]]', '[[Pontyjska Wikipedia|pontyjska]]'],
        'ps':['[[Pasztuńska Wikipedia|pasztuńska]]', '[[Pasztuńska Wikipedia|pasztuńska]]'],
        'pt':['[[Portugalskojęzyczna Wikipedia|portugalska]]', '[[Portugalskojęzyczna Wikipedia|portugalska]]'],
        'qu':['[[Wikipedia w języku keczua|keczua]]', '[[Wikipedia w języku keczua|keczua]]'],
        'rm':['[[Romanszska Wikipedia|romanszska]]', '[[Romanszska Wikipedia|romanszska]]'],
        'rmy':['[[Wikipedia w języku romskim (vlax)|romska (vlax)]]', '[[Wikipedia w języku romskim (vlax)|romska (vlax)]]'],
        'rn':['[[Rundyjska Wikipedia|rundyjska]]', '[[Rundyjska Wikipedia|rundyjska]]'],
        'ro':['[[Rumuńska Wikipedia|rumuńska]]', '[[Rumuńska Wikipedia|rumuńska]]'],
        'roa-rup':['[[Arumuńska Wikipedia|arumuńska]]', '[[Arumuńska Wikipedia|arumuńska]]'],
        'roa-tara':['[[Tarencka Wikipedia|tarencka]]', '[[Tarencka Wikipedia|tarencka]]'],
        'ru':['[[Rosyjskojęzyczna Wikipedia|rosyjska]]', '[[Rosyjskojęzyczna Wikipedia|rosyjska]]'],
        'rue':['[[Rusińska Wikipedia|rusińska]]', '[[Rusińska Wikipedia|rusińska]]'],
        'rw':['[[Wikipedia w języku ruanda-rundi|ruanda-rundi]]', '[[Wikipedia w języku ruanda-rundi|ruanda-rundi]]'],
        'sa':['[[Wikipedia w sanskrycie|w sanskrycie]]', '[[Wikipedia w sanskrycie|w sanskrycie]]'],
        'sah':['[[Jakucka Wikipedia|jakucka]]', '[[Jakucka Wikipedia|jakucka]]'],
        'sc':['[[Sardyńska Wikipedia|sardyńska]]', '[[Sardyńska Wikipedia|sardyńska]]'],
        'scn':['[[Sycylijska Wikipedia|sycylijska]]', '[[Sycylijska Wikipedia|sycylijska]]'],
        'sco':['[[Wikipedia w języku scots|szkocka]]', '[[Wikipedia w języku scots|szkocka]]'],
        'sd':['[[Wikipedia w języku sindhi|sindhi]]', '[[Wikipedia w języku sindhi|sindhi]]'],
        'se':['[[Północnolapońska Wikipedia|północnolapońska]]', '[[Północnolapońska Wikipedia|północnolapońska]]'],
        'sg':['[[Sangiańska Wikipedia|sangiańska]]', '[[Sangiańska Wikipedia|sangiańska]]'],
        'sh':['[[Serbsko-chorwacka Wikipedia|serbsko-chorwacka]]', '[[Serbsko-chorwacka Wikipedia|serbsko-chorwacka]]'],
        'si':['[[Edycje językowe Wikipedii#S|syngaleska]]', '[[Syngaleska Wikipedia|syngaleska]]'],
        'simple':['[[Wikipedia w języku Simple English|angielska uproszczona]]', '[[Wikipedia w języku Simple English|angielska uproszczona]]'],
        'sk':['[[Słowacka Wikipedia|słowacka]]', '[[Słowacka Wikipedia|słowacka]]'],
        'sl':['[[Słoweńska Wikipedia|słoweńska]]', '[[Słoweńska Wikipedia|słoweńska]]'],
        'sm':['[[Samoańska Wikipedia|samoańska]]', '[[Samoańska Wikipedia|samoańska]]'],
        'sn':['[[Shońska Wikipedia|shońska]]', '[[Shońska Wikipedia|shońska]]'],
        'so':['[[Somalijska Wikipedia|somalijska]]', '[[Somalijska Wikipedia|somalijska]]'],
        'sq':['[[Albańska Wikipedia|albańska]]', '[[Albańska Wikipedia|albańska]]'],
        'sr':['[[Serbska Wikipedia|serbska]]', '[[Serbska Wikipedia|serbska]]'],
        'srn':['[[Wikipedia w jezyku sranan tongo|surinamska]]', '[[Wikipedia w jezyku sranan tongo|surinamska]]'],
        'ss':['[[Wikipedia w języku suazi|suazi]]', '[[Wikipedia w języku suazi|suazi]]'],
        'st':['[[Sotyjska Wikipedia|sotyjska]]', '[[Sotyjska Wikipedia|sotyjska]]'],
        'stq':['[[Wikipedia w języku fryzyjskim saterlandzkim|fryzyjska saterlandzka]]', '[[Wikipedia w języku fryzyjskim saterlandzkim|fryzyjska saterlandzka]]'],
        'su':['[[Sundajska Wikipedia|sundajska]]', '[[Sundajska Wikipedia|sundajska]]'],
        'sv':['[[Szwedzka Wikipedia|szwedzka]]', '[[Szwedzka Wikipedia|szwedzka]]'],
        'sw':['[[Suahilijska Wikipedia|suahilijska]]', '[[Suahilijska Wikipedia|suahilijska]]'],
        'szl':['[[Śląska Wikipedia|śląska]]', '[[Śląska Wikipedia|śląska]]'],
        'ta':['[[Tamilska Wikipedia|tamilska]]', '[[Tamilska Wikipedia|tamilska]]'],
        'tcy':['[[Wikipedia w języku tulu|tulu]]', '[[Wikipedia w języku tulu|tulu]]'],
        'te':['[[Wikipedia w języku telugu|telugu]]', '[[Wikipedia w języku telugu|telugu]]'],
        'tet':['[[Tetumska Wikipedia|tetumska]]', '[[Tetumska Wikipedia|tetumska]]'],
        'tg':['[[Tadżycka Wikipedia|tadżycka]]', '[[Tadżycka Wikipedia|tadżycka]]'],
        'th':['[[Tajska Wikipedia|tajska]]', '[[Tajska Wikipedia|tajska]]'],
        'ti':['[[Tigrińska Wikipedia|tigrińska]]', '[[Tigrińska Wikipedia|tigrińska]]'],
        'tk':['[[Turkmeńska Wikipedia|turkmeńska]]', '[[Turkmeńska Wikipedia|turkmeńska]]'],
        'tl':['[[Wikipedia w języku tagalog|tagalska]]', '[[Wikipedia w języku tagalog|tagalska]]'],
        'tn':['[[Tswańska Wikipedia|tswańska]]', '[[Tswańska Wikipedia|tswańska]]'],
        'to':['[[Tongijska Wikipedia|tongijska]]', '[[Tongijska Wikipedia|tongijska]]'],
        'tpi':['[[Wikipedia w języku Tok pisin|Tok pisin]]', '[[Wikipedia w języku Tok pisin|Tok pisin]]'],
        'tr':['[[Turecka Wikipedia|turecka]]', '[[Turecka Wikipedia|turecka]]'],
        'ts':['[[Wikipedia w języku tsonga|tsonga]]', '[[Wikipedia w języku tsonga|tsonga]]'],
        'tt':['[[Tatarska Wikipedia|tatarska]]', '[[Tatarska Wikipedia|tatarska]]'],
        'tum':['[[Tumbucka Wikipedia|tumbucka]]', '[[Tumbucka Wikipedia|tumbucka]]'],
        'tw':['[[Wikipedia w języku twi|twi]]', '[[Wikipedia w języku twi|twi]]'],
        'ty':['[[Tahitańska Wikipedia|tahitańska]]', '[[Tahitańska Wikipedia|tahitańska]]'],
        'tyv':['[[Tuwińska Wikipedia|tuwińska]]', '[[Tuwińska Wikipedia|tuwińska]]'],
        'udm':['[[Udmurcka Wikipedia|udmurcka]]', '[[Udmurcka Wikipedia|udmurcka]]'],
        'ug':['[[Edycje językowe Wikipedii#U|ujguryjska]]', '[[Ujguryjska Wikipedia|ujguryjska]]'],
        'uk':['[[Ukraińska Wikipedia|ukraińska]]', '[[Ukraińska Wikipedia|ukraińska]]'],
        'ur':['[[Wikipedia w języku urdu|urdu]]', '[[Wikipedia w języku urdu|urdu]]'],
        'uz':['[[Uzbecka Wikipedia|uzbecka]]', '[[Uzbecka Wikipedia|uzbecka]]'],
        've':['[[Vendańska Wikipedia|vendańska]]', '[[Vendańska Wikipedia|vendańska]]'],
        'vec':['[[Wenecka Wikipedia|wenecka]]', '[[Wenecka Wikipedia|wenecka]]'],
        'vep':['[[Wepska Wikipedia|wepska]]', '[[Wepska Wikipedia|wepska]]'],
        'vi':['[[Wietnamska Wikipedia|wietnamska]]', '[[Wietnamska Wikipedia|wietnamska]]'],
        'vls':['[[Flamandzka Wikipedia|flamandzka]]', '[[Flamandzka Wikipedia|flamandzka]]'],
        'vo':['[[Wikipedia w języku volapük|volapük]]', '[[Wikipedia w języku volapük|volapük]]'],
        'wa':['[[Walońska Wikipedia|walońska]]', '[[Walońska Wikipedia|walońska]]'],
        'war':['[[Wikipedia w języku warajskim|warajska]]', '[[Wikipedia w języku warajskim|warajska]]'],
        'wo':['[[Wolofska Wikipedia|wolofska]]', '[[Wolofska Wikipedia|wolofska]]'],
        'wuu':['[[Wikipedia w języku wu|wu]]', '[[Wikipedia w języku wu|wu]]'],
        'xal':['[[Kałmucka Wikipedia|kałmucka]]', '[[Kałmucka Wikipedia|kałmucka]]'],
        'xh':['[[Wikipedia w języku xhosa|xhosa]]', '[[Wikipedia w języku xhosa|xhosa]]'],
        'xmf':['[[Megrelska Wikipedia|megrelska]]', '[[Megrelska Wikipedia|megrelska]]'],
        'yi':['[[Wikipedia w języku jidysz|jidysz]]', '[[Wikipedia w języku jidysz|jidysz]]'],
        'yo':['[[Wikipedia w języku joruba|joruba]]', '[[Wikipedia w języku joruba|joruba]]'],
        'za':['[[Wikipedia w języku zhuang|zhuang]]', '[[Wikipedia w języku zhuang|zhuang]]'],
        'zea':['[[Zelandzka Wikipedia|zelandzka]]', '[[Zelandzka Wikipedia|zelandzka]]'],
        'zh':['[[Chińska Wikipedia|chińska]]', '[[Chińska Wikipedia|chińska]]'],
        'zh-classical':['[[Wikipedia w klasycznym języku chińskim|chińska klasyczna]]', '[[Wikipedia w klasycznym języku chińskim|chińska klasyczna]]'],
        'zh-min-nan':['[[Minnańska Wikipedia|minnańska]]', '[[Minnańska Wikipedia|minnańska]]'],
        'zh-yue':['[[Kantońska Wikipedia|kantońska]]', '[[Kantońska Wikipedia|kantońska]]'],
        'zu':['[[Edycje językowe Wikipedii#Z|zuluska]]', '[[Zuluska Wikipedia|zuluska]]'],
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
            'summary': None,  # your own bot summary
            'outpage': u'Wikipedysta:mastiBot/test', #default output page
            'test': False, #switch on test functionality
            'edit': False, #link thru template:edytuj instead of wikilink
            'progress': False, # report progress
            'new': False, #generate using new (full) article names)
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

    def wikipedia(self,lang):
        #return link to article on pl.wiki
        if lang in self.wikipedias.keys():
            if self.getOption('new'):
                return(self.wikipedias[lang][1])
            else:
                return(self.wikipedias[lang][0])
        else:
            return(u'')

    def datepl(self):
        #return string for pl date
        months = ['stycznia','lutego','marca','kwietnia','maja','czerwca','lipca','sierpnia','wrzesnia','października','listopada','grudnia']
        return(re.sub(ur' \d* ',' '+months[int(datetime.datetime.now().strftime("%m"))-1]+' ',datetime.datetime.now().strftime("%-d %m %Y")))

    def assemblepage(self,artslists):
        # generate final page
        sections = ['5 000 000+', '2 000 000+', '1 000 000+', '500 000+', '200 000+', '100 000+', '50 000+', '25 000+', '10 000+', 'pozostałe' ]


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

        limits = [ 5000000, 2000000, 1000000, 500000, 200000, 100000, 50000, 25000, 10000, 0 ]
        artlists = {0:[],1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[]}

        #pywikibot.output(finalpage)

        res = sorted(redirlist, key=redirlist.__getitem__, reverse=True)
        if self.getOption('test'):
            pywikibot.output(res)

        section = 0
        for w in res:
            #pywikibot.output('w:%s:%i' % (self.wikipedias[w],redirlist[w]))
            if redirlist[w] < limits[section]:
                section +=1
            #if section > 8:
            #    break
            artlists[section].append('%s ([[:%s:]])' % (self.wikipedia(w),w))
        
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
        #wikiR = re.compile(ur"(?s)\| \[\[:(?P<lang>[\w-]*):.*?'''(?P<size>[\d,]*)")
        wikiR = re.compile(ur"\|-\n\| (?P<pos>\d*)\n\|.*?\|(?P<langen>.*?)\]\]\n\|.*?\}\} (?P<langloc>.*?)\]\n.*?\| \[\[:(?P<code>[\w-]*):.*?\n\|.*?'''(?P<size>[\d,]*).*?\n\| *(?P<pages>[\d,]*)\n\|.*?\|(?P<edits>[\d,]*)\]\]\n\|.*?\|(?P<admins>[\d,]*)\]\]\n\|.*?\|(?P<users>[\d,]*)\]\]\n\|.*?\|(?P<activeusers>[\d,]*)\]\]\n\|.*?\|(?P<files>[\d,]*)\]\]\n\| *(?P<depth>[\d]*)")

        result = {}
        unknownwiki = []
        count = 1
        for w in wikiR.finditer(text):
            lang = w.group('code')
            size = int(re.sub(ur',','',w.group('size')))
            wiki = self.wikipedia(lang)
            result[lang] = size
            if self.getOption('test'):
                pywikibot.output(u'[%s][%i]L:%s W:%s S:%i' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), count, lang, wiki, size ))
            count += 1
        if self.getOption('test'):
            #pywikibot.output(unknownwiki)
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
