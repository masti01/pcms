#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot creates a pages with links to disambig pages with ref counts.
Wikipedysta:MastiBot/Statystyka martwych linków
Wikipedysta:MastiBot/Statystyka martwych linków/ogólne

Call: 
python pwb.py masti/ms-deadlinks.py -cat:"Niezweryfikowane martwe linki" -ns:1 -outpage:"Wikipedysta:MastiBot/Statystyka martwych linków" -summary:"Bot uaktualnia stronę" -maxlines:3000

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

-includes:        Link to be searched for
-progress:        Display progress
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
import datetime
#import api


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

spamfilter = [
    re.compile(r'.*[\./@]ololol\.hpu\.pl(/.*)?'),
    re.compile(r'.*[\./@]porno\.org\.pl(/.*)?'),
    re.compile(r'.*[\./@]aitech\.pl(/.*)?'),
    re.compile(r'.*[\./@]kino-porno\.pl(/.*)?'),
    re.compile(r'.*[\./@]galerie-erotyczne\.pl(/.*)?'),
    re.compile(r'.*[\./@]wikileaks\.biz\.pl(/.*)?'),
    re.compile(r'.*[\./@]domnamazurach\.strefa\.pl(/.*)?'),
    re.compile(r'.*[\./@]brzozowiak\.pl(/.*)?'),
    re.compile(r'.*[\./@]roadlook\.pl(/.*)?'),
    re.compile(r'.*[\./@]emmashapplin\.org\.ar(/.*)?'),
    re.compile(r'.*[\./@]emmashapplin\.ovh\.pl(/.*)?'),
    re.compile(r'.*[\./@]chfang\.com(/.*)?'),
    re.compile(r'.*[\./@]\.az\.pl(/.*)?'),
    re.compile(r'.*[\./@]tvseriale\.pl(/.*)?'),
    re.compile(r'.*[\./@]kliknijtu\.1k\.pl(/.*)?'),
    re.compile(r'.*[\./@]launching\.blox\.pl(/.*)?'),
    re.compile(r'.*[\./@]onetskype\.pl(/.*)?'),
    re.compile(r'.*[\./@]mns\.ocom\.pl (/.*)?'),
    re.compile(r'.*[\./@]europa21\.pl(/.*)?'),
    re.compile(r'.*[\./@]eurojihad\.org(/.*)?'),
    re.compile(r'.*[\./@]beatbox\.be(/.*)?'),
    re.compile(r'.*[\./@]wlecce\.it(/.*)?'),
    re.compile(r'.*[\./@]leccesidentro\.it(/.*)?'),
    re.compile(r'.*[\./@]project\.jmp\.com\.pl(/.*)?'),
    re.compile(r'.*[\./@]tgfansite\.pl (/.*)?'),
    re.compile(r'.*[\./@]tizianoferropl\.netsons\.org(/.*)?'),
    re.compile(r'.*[\./@]tizianoferro\.xt\.pl(/.*)?'),
    re.compile(r'.*[\./@]c32\.pl(/.*)?'),
    re.compile(r'.*[\./@]metaldamage\.onet\.pl(/.*)?'),
    re.compile(r'.*[\./@]europedia\.moussis\.eu(/.*)?'),
    re.compile(r'.*[\./@]simy\.pl(/.*)?'),
    re.compile(r'.*[\./@]splywy\.pl(/.*)?'),
    re.compile(r'.*[\./@]krutynia\.com\.pl(/.*)?'),
    re.compile(r'.*[\./@]muzklasyczna\.prv\.pl(/.*)?'),
    re.compile(r'.*[\./@]daymonstudio\.pl(/.*)?'),
    re.compile(r'.*[\./@]baltimorepsychobilly\.com(/.*)?'),
    re.compile(r'.*[\./@]4x4rally\.pl(/.*)?'),
    re.compile(r'.*[\./@]ekabarety\.net(/.*)?'),
    re.compile(r'.*[\./@]kwiaty\.com(/.*)?'),
    re.compile(r'.*[\./@]i-jaroslaw\.pl(/.*)?'),
    re.compile(r'.*[\./@]s\d+\.battleknight\.onet\.pl(/.*)?'),
    re.compile(r'.*[\./@]s\d+\.bitefight\.onet\.pl(/.*)?'),
    re.compile(r'.*[\./@]s\d+\.gladiatus\.onet\.pl(/.*)?'),
    re.compile(r'.*[\./@]sebafoto\.com(/.*)?'),
    re.compile(r'.*[\./@]tykocin\.podlaskie\.pl(/.*)?'),
    re.compile(r'.*[\./@]wisla--krakow\.cba\.pl(/.*)?'),
    re.compile(r'.*[\./@]mochola\.org(/.*)?'),
    re.compile(r'.*[\./@]powiatchrzanowski\.pl(/.*)?'),
    re.compile(r'.*[\./@]totej\.pl\.tl(/.*)?'),
    re.compile(r'.*[\./@]kupiski\.blog\.onet\.pl(/.*)?'),
    re.compile(r'.*[\./@]andrzejbuda\.blog\.onet\.pl(/.*)?'),
    re.compile(r'.*[\./@]bigbrothervip\.com\.pl(/.*)?'),
    re.compile(r'.*[\./@]oboj\.am\.katowice\.pl(/.*)?'),
    re.compile(r'.*[\./@]zniczpruszkow\.com\.pl(/.*)?'),
    re.compile(r'.*[\./@]sashastrunin\.pl(/.*)?'),
    re.compile(r'.*[\./@]smolany\.ocom\.pl(/.*)?'),
    re.compile(r'.*[\./@]radio-tube\.pl(/.*)?'),
    re.compile(r'.*[\./@]juve24h\.yoyo\.pl(/.*)?'),
    re.compile(r'.*[\./@]katherinekellylang\.fora\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.ekademia\.pl(/.*)?'),
    re.compile(r'.*[\./@]reedukacja\.pl(/.*)?'),
    re.compile(r'.*[\./@]abbamusic\.bloog\.pl(/.*)?'),
    re.compile(r'.*[\./@]telewizja\.p20p\.pl(/.*)?'),
    re.compile(r'.*[\./@]turystykon\.pl(/.*)?'),
    re.compile(r'.*[\./@]budyń\.pl(/.*)?'),
    re.compile(r'.*[\./@]a4club\.eu(/.*)?'),
    re.compile(r'.*[\./@]faustina\.eu(/.*)?'),
    re.compile(r'.*[\./@]mlodagoldap\.info(/.*)?'),
    re.compile(r'.*[\./@]starsex\.pl(/.*)?'),
    re.compile(r'.*[\./@]lockerz\.com(/.*)?'),
    re.compile(r'.*[\./@]milenas\.xn\.pl(/.*)?'),
    re.compile(r'.*[\./@]milenas\.dbv\.pl(/.*)?'),
    re.compile(r'.*[\./@]milenasadurek\.cba\.pl(/.*)?'),
    re.compile(r'.*[\./@]wykonawca\.emuzyka\.pl(/.*)?'),
    re.compile(r'.*[\./@]warszawa360\.pl(/.*)?'),
    re.compile(r'.*[\./@]rankingofe\.com(/.*)?'),
    re.compile(r'.*[\./@]centrumofe\.com(/.*)?'),
    re.compile(r'.*[\./@]pageonetraffic\.co\.uk(/.*)?'),
    re.compile(r'.*[\./@]enortec\.com(/.*)?'),
    re.compile(r'.*[\./@]entrylevel-careers\.com(/.*)?'),
    re.compile(r'.*[\./@]caringbox\.co\.uk(/.*)?'),
    re.compile(r'.*[\./@]feelbettercenter\.com(/.*)?'),
    re.compile(r'.*[\./@]peb\.pl(/.*)?'),
    re.compile(r'.*[\./@]warkacider\.com(/.*)?'),
    re.compile(r'.*[\./@]zoba\.to(/.*)?'),
    re.compile(r'.*[\./@]faraon24\.pl(/.*)?'),
    re.compile(r'.*[\./@]sadistic\.pl(/.*)?'),
    re.compile(r'.*[\./@]iparts\.pl(/.*)?'),
    re.compile(r'.*[\./@]centrum-kore\.pl(/.*)?'),
    re.compile(r'.*[\./@]gtaultimate\.net(/.*)?'),
    re.compile(r'.*[\./@]gtasite\.pl(/.*)?'),
    re.compile(r'.*[\./@]gtaonline\.info(/.*)?'),
    re.compile(r'.*[\./@]gtaog\.eu(/.*)?'),
    re.compile(r'.*[\./@]gta\.imro\.pl(/.*)?'),
    re.compile(r'.*[\./@]cheats\.name(/.*)?'),
    re.compile(r'.*[\./@]gta-zone\.pl(/.*)?'),
    re.compile(r'.*[\./@]gamend\.net(/.*)?'),
    re.compile(r'.*[\./@]falloutcenter\.info(/.*)?'),
    re.compile(r'.*[\./@]kakolukia\.yoyo\.pl(/.*)?'),
    re.compile(r'.*[\./@]liveupdatesnet\.com(/.*)?'),
    re.compile(r'.*[\./@]scepter\.pl(/.*)?'),
    re.compile(r'.*[\./@]flashstar\.pl(/.*)?'),
    re.compile(r'.*[\./@]sztab\.com(/.*)?'),
    re.compile(r'.*[\./@]civ\.org\.pl(/.*)?'),
    re.compile(r'.*[\./@]codjumper\.pl(/.*)?'),
    re.compile(r'.*[\./@]xboxxn\.com(/.*)?'),
    re.compile(r'.*[\./@]amarantt\.org(/.*)?'),
    re.compile(r'.*[\./@]warszawa78\.blox\.pl(/.*)?'),
    re.compile(r'.*[\./@]kominek\.blox\.pl(/.*)?'),
    re.compile(r'.*[\./@]welcomeurope\.com(/.*)?'),
    re.compile(r'.*[\./@]ratowice\.phorum\.pl(/.*)?'),
    re.compile(r'.*[\./@]eastway\.pl(/.*)?'),
    re.compile(r'.*[\./@]eko-pol\.pl(/.*)?'),
    re.compile(r'.*[\./@]korepetycjeszczecin\.pl(/.*)?'),
    re.compile(r'.*[\./@]vampiresforever\.mojeforum\.net(/.*)?'),
    re.compile(r'.*[\./@]iq-test\.pl(/.*)?'),
    re.compile(r'.*[\./@]HRtrendy\.pl (/.*)?'),
    re.compile(r'.*[\./@]li8li\.com(/.*)?'),
    re.compile(r'.*[\./@]ski-russia\.net(/.*)?'),
    re.compile(r'.*[\./@]visionki\.pl(/.*)?'),
    re.compile(r'.*[\./@]betispoland\.com(/.*)?'),
    re.compile(r'.*[\./@]kod-zbawienia\.home\.pl(/.*)?'),
    re.compile(r'.*[\./@]dobry-portal\.pl(/.*)?'),
    re.compile(r'.*[\./@]prepedia\.wikia\.com(/.*)?'),
    re.compile(r'.*[\./@]oriflame4u\.pl(/.*)?'),
    re.compile(r'.*[\./@]my\.oriflame\.pl(/.*)?'),
    re.compile(r'.*[\./@]czornij\.pl (/.*)?'),
    re.compile(r'.*[\./@]\.on\.nimp\.org(/.*)?'),
    re.compile(r'.*[\./@]bojownik\.pl(/.*)?'),
    re.compile(r'.*[\./@]zawisaki\.republika\.pl(/.*)?'),
    re.compile(r'.*[\./@]haniastach\.fan\.pl(/.*)?'),
    re.compile(r'.*[\./@]iqpolska\.pl(/.*)?'),
    re.compile(r'.*[\./@]slwiki\.e-woody\.info(/.*)?'),
    re.compile(r'.*[\./@]eutanazja\.info(/.*)?'),
    re.compile(r'.*[\./@]galeria\.reszel\.pl(/.*)?'),
    re.compile(r'.*[\./@]e\-inquiry\.eu(/.*)?'),
    re.compile(r'.*[\./@]evolver\.pl(/.*)?'),
    re.compile(r'.*[\./@]atlasofchurch\.altervista\.org(/.*)?'),
    re.compile(r'.*[\./@]n69\.pl(/.*)?'),
    re.compile(r'.*[\./@]sjp\.pl(/.*)?'),
    re.compile(r'.*[\./@]pomponik\.pl(/.*)?'),
    re.compile(r'.*[\./@]pudelek\.pl(/.*)?'),
    re.compile(r'.*[\./@]kozaczek\.pl(/.*)?'),
    re.compile(r'.*[\./@]widelec\.pl(/.*)?'),
    re.compile(r'.*[\./@]plotek\.pl(/.*)?'),
    re.compile(r'.*[\./@]proakvariumy\.ru(/.*)?'),
    re.compile(r'.*[\./@]polonica\.net(/.*)?'),
    re.compile(r'.*[\./@]ligol\.pl(/.*)?'),
    re.compile(r'.*[\./@]rrgranity\.pl(/.*)?'),
    re.compile(r'.*[\./@]koktajl24\.pl(/.*)?'),
    re.compile(r'.*[\./@]gadulek\.pl(/.*)?'),
    re.compile(r'.*[\./@]apcchart\.com(/.*)?'),
    re.compile(r'.*[\./@]euro200\.net(/.*)?'),
    re.compile(r'.*[\./@]kotek\.pl(/.*)?'),
    re.compile(r'.*[\./@]lansik\.pl(/.*)?'),
    re.compile(r'.*[\./@]obmawiamy\.pl(/.*)?'),
    re.compile(r'.*[\./@]klopsik\.pl(/.*)?'),
    re.compile(r'.*[\./@]aleplotka\.pl(/.*)?'),
    re.compile(r'.*[\./@]kaprysek\.pl(/.*)?'),
    re.compile(r'.*[\./@]wpadki\.pl(/.*)?'),
    re.compile(r'.*[\./@]egoisci\.pl(/.*)?'),
    re.compile(r'.*[\./@]zeberka\.pl(/.*)?'),
    re.compile(r'.*[\./@]plotka\.pl(/.*)?'),
    re.compile(r'.*[\./@]poselska\.nazwa\.pl(/.*)?'),
    re.compile(r'.*[\./@]niewiarygodne\.pl(/.*)?'),
    re.compile(r'.*[\./@]tajemniczyswiat\.com\.pl(/.*)?'),
    re.compile(r'.*[\./@]bialczynski\.wordpress\.com(/.*)?'),
    re.compile(r'.*[\./@]forex-informacje\.blogspot\.com(/.*)?'),
    re.compile(r'.*[\./@]zmianynaziemi\.pl(/.*)?'),
    re.compile(r'.*[\./@]losyziemi\.pl(/.*)?'),
    re.compile(r'.*[\./@]wladcy\.myslenice\.net\.pl(/.*)?'),
    re.compile(r'.*[\./@]jewornotjew\.com(/.*)?'),
    re.compile(r'.*[\./@]www\.poradnikzdrowie\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.dlarodzinki\.pl/male-dziecko/zdrowie(/.*)?'),
    re.compile(r'.*[\./@]bogowie\.org\.pl (/.*)?'),
    re.compile(r'.*[\./@]encyklopedia\.naukowy\.pl(/.*)?'),
    re.compile(r'.*[\./@]kamienne\.org\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.vismaya-maitreya\.pl(/.*)?'),
    re.compile(r'.*[\./@]nowaatlantyda\.com(/.*)?'),
    re.compile(r'.*[\./@]praslowianie\.pl(/.*)?'),
    re.compile(r'.*[\./@]infra\.org\.pl(/.*)?'),
    re.compile(r'.*[\./@]nautilus\.org\.pl(/.*)?'),
    re.compile(r'.*[\./@]potop-exodus\.w\.interia\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.olabloga\.pl(/.*)?'),
    re.compile(r'.*[\./@]translate\.google\.com(/.*)?'),
    re.compile(r'.*[\./@]prepedia\.wikia\.com(/.*)?'),
    re.compile(r'.*[\./@]lovekrakow\.pl(/.*)?'),
    re.compile(r'.*[\./@]wolnemedia\.net(/.*)?'),
    re.compile(r'.*[\./@]wolnemedia\.pl(/.*)?'),
    re.compile(r'.*[\./@]\bnieznane\.pl(/.*)?'),
    re.compile(r'.*[\./@]paranormalne\.eu(/.*)?'),
    re.compile(r'.*[\./@]paranormalne\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.node81\.tsi\.net\.pl(/.*)?'),
    re.compile(r'.*[\./@]chemia\.gbzl\.pl(/.*)?'),
    re.compile(r'.*[\./@]\.umysl\.pl(/.*)?'),
    re.compile(r'.*[\./@]\/umysl\.pl(/.*)?'),
    re.compile(r'.*[\./@]michalpasterski\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.prezentacje-maturalne\.pl(/.*)?'),
    re.compile(r'.*[\./@]dubbingpedia\.pl(/.*)?'),
    re.compile(r'.*[\./@]zbawienie\.com(/.*)?'),
    re.compile(r'.*[\./@]proroctwa\.com(/.*)?'),
    re.compile(r'.*[\./@]pierwszyportal\.pl(/.*)?'),
    re.compile(r'.*[\./@]historycy\.org(/.*)?'),
    re.compile(r'.*[\./@]flickeringmyth\.com (/.*)?'),
    re.compile(r'.*[\./@]ciekawostkihistoryczne\.pl(/.*)?'),
    re.compile(r'.*[\./@]wolna-polska\.pl(/.*)?'),
    re.compile(r'.*[\./@]tekstowo\.pl(/.*)?'),
    re.compile(r'.*[\./@]bryk\.pl(/.*)?'),
    re.compile(r'.*[\./@]kulturadobra\.pl(/.*)?'),
    re.compile(r'.*[\./@]wypracowania24\.pl(/.*)?'),
    re.compile(r'.*[\./@]sciaga\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.wikalim\.republika\.pl(/.*)?'),
    re.compile(r'.*[\./@]zadane\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.znamlek\.pl(/.*)?'),
    re.compile(r'.*[\./@]jehowa\.info(/.*)?'),
    re.compile(r'.*[\./@]jehowa-biblioteka\.com(/.*)?'),
    re.compile(r'.*[\./@]www\.megapower\.pl(/.*)?'),
    re.compile(r'.*[\./@]alexjones\.pl(/.*)?'),
    re.compile(r'.*[\./@]klp\.pl(/.*)?'),
    re.compile(r'.*[\./@]krzyzowki\.info(/.*)?'),
    re.compile(r'.*[\./@]biblia\.oblubienica\.eu(/.*)?'),
    re.compile(r'.*[\./@]bialczynski\.pl(/.*)?'),
    re.compile(r'.*[\./@]innemedium\.pl(/.*)?'),
    re.compile(r'.*[\./@]sbb-music.jimdo\.com(/.*)?'),
    re.compile(r'.*[\./@]sfora\.pl(/.*)?'),
    re.compile(r'.*[\./@]niewygodne\.info\.pl(/.*)?'),
    re.compile(r'.*[\./@]niepoprawni\.pl(/.*)?'),
    re.compile(r'.*[\./@]historio\.pl(/.*)?'),
    re.compile(r'.*[\./@]prisonplanet\.pl(/.*)?'),
    re.compile(r'.*[\./@]himavanti\.org(/.*)?'),
    re.compile(r'.*[\./@]niezaleznatelewizja\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.monitor-polski\.pl(/.*)?'),
    re.compile(r'.*[\./@]pl\.staratelewizja\.wikia\.com(/.*)?'),
    re.compile(r'.*[\./@]revolvy\.com(/.*)?'),
    re.compile(r'.*[\./@]historia\.na6\.pl(/.*)?'),
    re.compile(r'.*[\./@]geografia\.na6\.pl(/.*)?'),
    re.compile(r'.*[\./@]angielski\.na6\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.polskina5\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.wosna5\.pl(/.*)?'),
    re.compile(r'.*[\./@]slowianieiukrytahistoriapolski\.pl(/.*)?'),
    re.compile(r'.*[\./@]brainly\.pl(/.*)?'),
    re.compile(r'.*[\./@]wypracowania\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.m\.opracowania\.pl(/.*)?'),
    re.compile(r'.*[\./@]nibiru\.pl(/.*)?'),
    re.compile(r'.*[\./@]en\.hortipedia\.com(/.*)?'),
    re.compile(r'.*[\./@]de\.hortipedia\.com(/.*)?'),
    re.compile(r'.*[\./@]fr\.hortipedia\.com(/.*)?'),
    re.compile(r'.*[\./@]przeczytaneksiazki\.pl(/.*)?'),
    re.compile(r'.*[\./@]wasze-opinie\.pl(/.*)?'),
    re.compile(r'.*[\./@]nasze-miasto24\.prv\.pl(/.*)?'),
    re.compile(r'.*[\./@]argonauta\.pl(/.*)?'),
    re.compile(r'.*[\./@]wiaraprzyrodzona\.wordpress\.com(/.*)?'),
    re.compile(r'.*[\./@]zegarsmierci\.info(/.*)?'),
    re.compile(r'.*[\./@]eduteka\.pl(/.*)?'),
    re.compile(r'.*[\./@]klubinteligencjipolskiej\.pl(/.*)?'),
    re.compile(r'.*[\./@]ivrozbiorpolski\.pl(/.*)?'),
    re.compile(r'.*[\./@]gazetawarszawska\.com(/.*)?'),
    re.compile(r'.*[\./@]polskabc\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.reformowani\.info(/.*)?'),
    re.compile(r'.*[\./@]wielkahistoria\.pl(/.*)?'),
    re.compile(r'.*[\./@]biografie-niemieckie\.pl(/.*)?'),
    re.compile(r'.*[\./@]prawicowyinternet\.pl(/.*)?'),
    re.compile(r'.*[\./@]pinkwall\.pl(/.*)?'),
    re.compile(r'.*[\./@]treborok\.wordpress\.com(/.*)?'),
    re.compile(r'.*[\./@]globalna\.info(/.*)?'),
    re.compile(r'.*[\./@]marucha\.wordpress\.com(/.*)?'),
    re.compile(r'.*[\./@]rudaweb\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.kontestator\.eu(/.*)?'),
    re.compile(r'.*[\./@]basileia785\.wordpress\.com(/.*)?'),
    re.compile(r'.*[\./@]szkolnictwo\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.udyomedia\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.naukowy\.pl/encyklopedia(/.*)?'),
    re.compile(r'.*[\./@]www\.naukowy\.pl/encyklo.php(/.*)?'),
    re.compile(r'.*[\./@]encyklopedia\.eduteka\.pl(/.*)?'),
    re.compile(r'.*[\./@]slowianie\.rolnicy\.com(/.*)?'),
    re.compile(r'.*[\./@]cyclopaedia\.net(/.*)?'),
    re.compile(r'.*[\./@]edu\.gazeta\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.zgapa\.pl/zgapedia/(/.*)?'),
    re.compile(r'.*[\./@]heltechnic\.pl(/.*)?'),
    re.compile(r'.*[\./@]ramotowscy\.pl(/.*)?'),
    re.compile(r'.*[\./@]encyklopedia\.malbork\.pl(/.*)?'),
    re.compile(r'.*[\./@]poland\.turystyka\.pl(/.*)?'),
    re.compile(r'.*[\./@]radioswissclassic\.ch/(en|de|fr|it)/(music-database|musikdatenbank|base-de-donnees-musicale|banca-dati-musicale)(/.*)?'),
    re.compile(r'.*[\./@]qwe\.wiki(/.*)?'),
    re.compile(r'.*[\./@]encyklopedia\.biolog\.pl(/.*)?'),
    re.compile(r'.*[\./@]dbpedia\.org(/.*)?'),
    re.compile(r'.*[\./@]lotter\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.wikalim\.republika\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.rumburak\.friko\.pl(/.*)?'),
    re.compile(r'.*[\./@]bandyckapolicja\.com(/.*)?'),
    re.compile(r'.*[\./@]www\.tygodniknaukowy\.pl(/.*)?'),
    re.compile(r'.*[\./@]snauka\.pl(/.*)?'),
    re.compile(r'.*[\./@]poezja\.org(/.*)?'),
    re.compile(r'.*[\./@]biblioteka\.kijowski\.pl(/.*)?'),
    re.compile(r'.*[\./@]zrodla\.historyczne\.prv\.pl(/.*)?'),
    re.compile(r'.*[\./@]odsiebie\.com/pokaz(/.*)?'),
    re.compile(r'.*[\./@]odsiebie\.com/plik(/.*)?'),
    re.compile(r'.*[\./@]rapidshare\.com/files(/.*)?'),
    re.compile(r'.*[\./@]hotfile\.com/dl(/.*)?'),
    re.compile(r'.*[\./@]sharingmatrix\.com/file(/.*)?'),
    re.compile(r'.*[\./@]chomikuj\.pl\/(/.*)?'),
    re.compile(r'.*[\./@]docer\.pl(/.*)?'),
    re.compile(r'.*[\./@]zanotowane\.pl(/.*)?'),
    re.compile(r'.*[\./@]twirpx\.com(/.*)?'),
    re.compile(r'.*[\./@]freedisc\.pl(/.*)?'),
    re.compile(r'.*[\./@]img*\.imageshack\.us(/.*)?'),
    re.compile(r'.*[\./@]pingwinojad\.blog\.pl(/.*)?'),
    re.compile(r'.*[\./@]bocian\.ugu\.pl(/.*)?'),
    re.compile(r'.*[\./@]ksiega\.ritcat\.pl(/.*)?'),
    re.compile(r'.*[\./@]ksiega\.4free\.pl(/.*)?'),
    re.compile(r'.*[\./@]brutalland\.webd\.pl(/.*)?'),
    re.compile(r'.*[\./@]akap\.wrzuta\.pl/audio/0BdsDTGltvO/biala_piesc_-_monopol_na_przemoc(/.*)?'),
    re.compile(r'.*[\./@]przetwarzaniemowy\.pl(/.*)?'),
    re.compile(r'.*[\./@]lowekrakow\.pl(/.*)?'),
    re.compile(r'.*[\./@]tandadoorco\.uk(/.*)?'),
    re.compile(r'.*[\./@]skarbiecmazowiecki\.pl(/.*)?'),
    re.compile(r'.*[\./@]v1agrabuy\.com(/.*)?'),
    re.compile(r'.*[\./@]www\.galeria-attis\.pl(/.*)?'),
    re.compile(r'.*[\./@]help-dysk\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.spotkania\.pl(/.*)?'),
    re.compile(r'.*[\./@]www\.supla\.org(/.*)?'),
    re.compile(r'.*[\./@]bridemageddon\.pl(/.*)?'),
    re.compile(r'.*[\./@]finaton\.pl(/.*)?'),
    re.compile(r'.*[\./@]kurs-waluty\.pl(/.*)?'),
    re.compile(r'.*[\./@]mooncanna\.pl(/.*)?'),
    re.compile(r'.*[\./@]grupa-tense\.pl(/.*)?'),
    re.compile(r'.*[\./@]seo-www\.pl(/.*)?'),
    re.compile(r'.*[\./@]emeraldmedia\.pl(/.*)?'),
    re.compile(r'.*[\./@]digitalhill\.pl(/.*)?'),
    re.compile(r'.*[\./@]kerrisselect\.pl(/.*)?'),
    re.compile(r'.*[\./@]widzialni\.pl(/.*)?'),
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
            'outpage': u'Wikipedysta:mastiBot/test', #default output page
            'maxlines': 1000, #default number of entries per page
            'test': False, #test options
            'progress':False, #display progress
            'includes' : False, #only include links that include this text
        })

        # call constructor of the super class
        super(BasicBot, self).__init__(site=True, **kwargs)
        #super(SingleSiteBot, self).__init__(site=True, **kwargs)

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

        if self.getOption('test'):
            pywikibot.output(self.getOption('includes'))

        headerfull = u"Poniżej znajduje się lista " + self.getOption('maxlines') + u" martwych linków występujących w największej liczbie artykułów.\n\n"
        headersum = headerfull
        if not self.getOption('includes'):
            headersum += u"Zobacz też: [[" + self.getOption('outpage') + u"|Statystykę szczegółowych linków]]\n\n"
            headerfull += u"Zobacz też: [[" + self.getOption('outpage') + u"/ogólne|Statystykę domen z największą liczbą martwych linków]]\n\n"

        headerfull += u"Ta strona jest okresowo uaktualniana przez [[Wikipedysta:MastiBot|MastiBota]]. Ostatnia aktualizacja ~~~~~. \n"
        headerfull += u"Wszelkie uwagi proszę zgłaszać w [[Dyskusja_Wikipedysty:Masti|dyskusji operatora]].\n\n"
        headersum += u"Ta strona jest okresowo uaktualniana przez [[Wikipedysta:MastiBot|MastiBota]]. Ostatnia aktualizacja ~~~~~. \n"
        headersum += u"Wszelkie uwagi proszę zgłaszać w [[Dyskusja_Wikipedysty:Masti|dyskusji operatora]].\n\n"
        footer = u''

        deadlinksf = {} #full links
        deadlinkss = {} #summary links
        deadlinksfuse = {} #full links
        deadlinkssuse = {} #summary links
        licznik = 0
        for page in self.generator:
            licznik += 1
            if self.getOption('progress'):
                pywikibot.output(u'[%s]Treating #%i: %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),licznik, page.title()))
            refs = self.treat(page) # get list of weblinks
            for ref,rcount in refs:
                #if self.getOption('test'):
                #    pywikibot.output('REFS: %s' % refs)
                if ref in deadlinksf:
                   deadlinksf[ref] += 1
                   deadlinksfuse[ref] += rcount
                else:
                   deadlinksf[ref] = 1
                   deadlinksfuse[ref] = rcount 
                if self.getOption('test'):
                    pywikibot.output(u'%s - %i' % (ref,deadlinksf[ref]))
            """ sitch of -domains option
            #TODO get domain form analysis of previous step
            refs = self.treat(page, True) # get list of weblinks
            for ref,rcount in refs:
                if ref in deadlinkss:
                   deadlinkss[ref] += 1
                   deadlinkssuse[ref] += rcount
                else:
                   deadlinkss[ref] = 1
                   deadlinkssuse[ref] = rcount
                if self.getOption('test'):
                    pywikibot.output(u'%s - %i' % (ref,deadlinkss[ref]))
            """
            #if licznik > self.maxlines-1:
            #    pywikibot.output(u'*** Breaking outer loop ***')
            #    break

        deadlinkss,deadlinkssuse = self.getDomainStats(deadlinksf,deadlinksfuse)

        footer = u'Przetworzono: ' + str(licznik) + u' stron'        

        result = self.generateresultspage(deadlinksf,deadlinksfuse,self.getOption('outpage'),headerfull,footer)
        # skip domains grouping if looking for specific text
        #if not self.getOption('includes'):
        result = self.generateresultspage(deadlinkss,deadlinkssuse,self.getOption('outpage')+u'/ogólne',headersum,footer)

    def getDomainStats(self,dl,dluse):
        deadlinksf = {}
        deadlinksfuse = {}
        domainR = re.compile(r'(?P<domain>https?://[^\/]*)')

        for l in dl.keys():
            try:
                dom = domainR.match(l).group('domain')
                if self.getOption('test'):
                    pywikibot.output('Domain:link:%s' % dom)
                if dom in deadlinksf.keys():
                    deadlinksf[dom] += dl[l]
                    deadlinksfuse[dom] += dluse[l]
                else:
                    deadlinksf[dom] = dl[l]
                    deadlinksfuse[dom] = dluse[l]
            except:
                pywikibot.output('Missing domain group in %s' % l)

        return(deadlinksf,deadlinksfuse)           

    def getRefsNumber(self,weblink,text):
        #find how many times link is referenced on the page
        # ref names including group
        #refR = re.compile(r'(?i)<ref (group *?= *?"?(?P<group>[^>"]*)"?)?(name *?= *?"?(?P<name>[^>"]*)"?)?>\.?\[?(?P<url>http[s]?:(\/\/[^:\s\?]+?)(\??[^\s<]*?)[^\]\.])(\]|\]\.)?[ \t]*<\/ref>')
        refR = re.compile(r'(?im)<ref (group *?= *?"?(?P<group>[^>"]*)"?)?(name *?= *?"?(?P<name>[^>"]*)"?)?>.*?%s.*?<\/ref>' % re.escape(weblink).strip())

        """
        opcje wywołania: <ref name="BVL2006" /> {{u|BVL2006}} {{r|BVL2006}}
        """

        #check if weblink is in named ref
        linkscount = 0
        #for r in refR.finditer(text):
        r = refR.search(text)
        if r:
            if r.group('name'):
                if self.getOption('test'):
                    pywikibot.output('Treat:NamedRef:%s' % r.group('name'))
                #template to catch note/ref with {{u}} or {{r}}
                ruR = re.compile(r'(?i)(?:{{[ur] *?(?:[^\|}]*\|)*|<ref *?name *?= *?\"?)(%s)(?:[^}\/]*}}|\"? \/>)' % re.escape(r.group('name').strip()))
                if self.getOption('test'):
                    pywikibot.output('Treat:Regex:(?i)(?:{{[ur] *?(?:[^\|}]*\|)*|<ref *?name *?= *?\"?)(%s)(?:[^}\/]*}}|\"? \/>)' % re.escape(r.group('name').strip()))
                match = ruR.findall(text)
                linkscount += len(match)
                if self.getOption('test'):
                    pywikibot.output('Treat:Templates matched:%s' % match)
        if self.getOption('test'):
            pywikibot.output('Treat:links count:%s' % linkscount)

        #catch unnamed links
        match = re.findall(re.escape(weblink),text)
        linkscount += len(match)
        if self.getOption('test'):
            pywikibot.output('Treat:Loose links matched:%s' % match)
            pywikibot.output('Treat:links count:%s' % linkscount)

        return(linkscount)

    def treat(self, page):
        """
        Creates a list of weblinks
        """
        refs = []
        tempR = re.compile(r'(?P<template>\{\{Martwy link dyskusja[^}]*?}}\n*?)')
        #weblinkR = re.compile(r'link\s*?=\s*?\*?\s*?(?P<weblink>[^\n\(]*)')
        weblinkR = re.compile(r'link *?= *?\*? (?P<weblink>[^\n ]*)')
        if self.getOption('test'):
            pywikibot.output(u'domains=False')
        links = u''
        art = page.toggleTalkPage()
        arttext = art.text
        templs = tempR.finditer(page.text)
        for link in templs:
            template = link.group('template').strip()
            if self.getOption('test'):
                pywikibot.output(template)
            try:
                weblink = re.search(weblinkR,template).group('weblink').strip()
            except:
                continue
            linkscount = self.getRefsNumber(weblink,arttext)
            refs.append( (weblink,linkscount) )
            if self.getOption('test'):
                    pywikibot.output('Treat Weblink:%s' % weblink)
                    pywikibot.output('Treat Usage:%i' % linkscount)
            #except:
            #    pywikibot.output(u'Error in page %s' % page.title(asLink=True))

        return(refs)

    def SpamCheck(self, url):
        r = pywikibot.data.api.Request(parameters={'action': 'spamblacklist', 'url': url})
        data = r.submit()
        return(data['spamblacklist']['result']=='blacklisted')
        

    def generateresultspage(self, redirlist, redirlistuse, pagename, header, footer):
        """
        Generates results page from redirlist
        Starting with header, ending with footer
        Output page is pagename
        """
        maxlines = int(self.getOption('maxlines'))
        finalpage = header
         
        finalpage +=u'\n{| class="wikitable sortable" style="font-size:85%;"'
        finalpage +=u'\n|-'
        finalpage +=u'\n!Nr'
        finalpage +=u'\n!Link'
        finalpage +=u'\n!Liczba stron'
        finalpage +=u'\n!Liczba odnośników'



        res = sorted(redirlist, key=redirlist.__getitem__, reverse=True)
        itemcount = 0
        pywikibot.output('res length:%i' % len(res))
        for i in res:
            # use only links with -includes if specified
            if self.getOption('includes'):
                if not (self.getOption('includes') in i):
                    continue

            # check for spamlist entry
            """
            for ignoreR in spamfilter:
                if ignoreR.match(i):
                    pywikibot.output("SPAM: ignoring link: [%s]" % i)
                    continue
            """
            pywikibot.output('CALLING SPAMCHECK')
            spam = self.SpamCheck(i)

            itemcount += 1
            count = redirlist[i]
            strcount = str(count)
            #suffix = self.declination(count, u'wystąpienie', u'wystąpienia', u'wystąpień')
            suffix = self.declination(count, u'strona', u'strony', u'stron')
            linksuffix = self.declination(redirlistuse[i], u'odnośnik', u'odnośniki', u'odnośników')

            #finalpage += u'#' + i + u' ([{{fullurl:Specjalna:Wyszukiwarka linków/|target=' + i + u'}} ' + str(count) + u' ' + suffix + u'])\n'
            if self.getOption('test'):
                pywikibot.output(u'(%d, %d) #%s (%s %s)' % (itemcount, len(finalpage), i, str(count), suffix))
            if spam:
                finalpage += u'\n|-\n| ' + str(itemcount) + u' || <nowiki>' + i + u'</nowiki><sup>SPAM</sup> || style="width: 20%;" align="center" | [{{fullurl:Specjalna:Wyszukiwarka linków/|target=' + i + u'}} ' + str(count) + u' ' + suffix + u']'
            else:
                finalpage += u'\n|-\n| ' + str(itemcount) + u' || ' + i + u' || style="width: 20%;" align="center" | [{{fullurl:Specjalna:Wyszukiwarka linków/|target=' + i + u'}} ' + str(count) + u' ' + suffix + u']'
            finalpage += u' || %i %s' % (redirlistuse[i],linksuffix)
            if itemcount > maxlines-1:
                pywikibot.output(u'*** Breaking output loop ***')
                break

        finalpage += u'\n|}\n'
        finalpage += footer 

        if self.getOption('test'):
            pywikibot.output(finalpage)
        success = True
        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        outpage.text = finalpage

        if self.getOption('test'):
            pywikibot.output(outpage.title())
        
        outpage.save(summary=self.getOption('summary'))
        return(success)

    def declination(self, v, t1, t2, t3):
        value = int(str(v)[-2:])
        if value == 0:
            return(t3)
        elif value == 1:
            return(t1)
        elif value < 5:
            return(t2)
        else:
            return(t3)



def templateArg(param):
        """
        return name,value for each template param

        input text in form "name = value"
        @return: a tuple for each param of a template
            named: named (True) or int
            name: name of param or None if numbered
            value: value of param
        @rtype: tuple
        """
        paramR = re.compile(r'(?P<name>.*)=(?P<value>.*)')
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
        if self.getOption('test'):
            pywikibot.output(u'named:%s:name:%s:value:%s' % (named, name, value))
        return(named, name, value)

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
        if option in ('summary', 'text', 'outpage', 'maxlines', 'includes'):
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
        return(True)
    else:
        pywikibot.bot.suggest_help(missing_generator=True)
        return(False)

if __name__ == '__main__':
    main()
