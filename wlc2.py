#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot is used for checking external links found at the wiki.

It checks several pages at once, with a limit set by the config variable
max_external_links, which defaults to 50.

The bot won't change any wiki pages, it will only report dead links such that
people can fix or remove the links themselves.

The bot will store all links found dead in a .dat file in the deadlinks
subdirectory. To avoid the removing of links which are only temporarily
unavailable, the bot ONLY reports links which were reported dead at least
two times, with a time lag of at least one week. Such links will be logged to a
.txt file in the deadlinks subdirectory.

The .txt file uses wiki markup and so it may be useful to post it on the
wiki and then exclude that page from subsequent runs. For example if the
page is named Broken Links, exclude it with '-titleregexnot:^Broken Links$'

After running the bot and waiting for at least one week, you can re-check those
pages where dead links were found, using the -repeat parameter.

In addition to the logging step, it is possible to automatically report dead
links to the talk page of the article where the link was found. To use this
feature, set report_dead_links_on_talk = True in your user-config.py, or
specify "-talk" on the command line. Adding "-notalk" switches this off
irrespective of the configuration variable.

When a link is found alive, it will be removed from the .dat file.

These command line parameters can be used to specify which pages to work on:

-repeat      Work on all pages were dead links were found before. This is
             useful to confirm that the links are dead after some time (at
             least one week), which is required before the script will report
             the problem.

-namespace   Only process templates in the namespace with the given number or
             name. This parameter may be used multiple times.

-xml         Should be used instead of a simple page fetching method from
             pagegenerators.py for performance and load issues

-xmlstart    Page to start with when using an XML dump

-ignore      HTTP return codes to ignore. Can be provided several times :
                -ignore:401 -ignore:500

&params;

Furthermore, the following command line parameters are supported:

-talk        Overrides the report_dead_links_on_talk config variable, enabling
             the feature.

-notalk      Overrides the report_dead_links_on_talk config variable, disabling
             the feature.

-day         Do not report broken link if the link is there only since
             x days or less. If not set, the default is 7 days.

The following config variables are supported:

 max_external_links         The maximum number of web pages that should be
                            loaded simultaneously. You should change this
                            according to your Internet connection speed.
                            Be careful: if it is set too high, the script
                            might get socket errors because your network
                            is congested, and will then think that the page
                            is offline.

 report_dead_links_on_talk  If set to true, causes the script to report dead
                            links on the article's talk page if (and ONLY if)
                            the linked page has been unavailable at least two
                            times during a timespan of at least one week.

 weblink_dead_days          sets the timespan (default: one week) after which
                            a dead link will be reported

Examples
--------

Loads all wiki pages in alphabetical order using the Special:Allpages
feature:

    python pwb.py weblinkchecker -start:!

Loads all wiki pages using the Special:Allpages feature, starting at
"Example page":

    python pwb.py weblinkchecker -start:Example_page

Loads all wiki pages that link to www.example.org:

    python pwb.py weblinkchecker -weblink:www.example.org

Only checks links found in the wiki page "Example page":

    python pwb.py weblinkchecker Example page

Loads all wiki pages where dead links were found during a prior run:

    python pwb.py weblinkchecker -repeat
"""
#
# (C) Pywikibot team, 2005-2020
#
# Distributed under the terms of the MIT license.
#
import codecs
import datetime
import http.client as httpclient
import pickle
import re
import socket
import threading
import time

from contextlib import suppress
from functools import partial
from typing import Optional, Tuple
from urllib.parse import urlsplit
from urllib.request import quote

import requests

import pywikibot

from pywikibot import comms, i18n, config, pagegenerators, textlib, config2

from pywikibot.bot import ExistingPageBot, SingleSiteBot, suggest_help
from pywikibot.pagegenerators import (
    XMLDumpPageGenerator as _XMLDumpPageGenerator,
)
from pywikibot.tools import deprecated, ThreadList
from pywikibot.tools.formatter import color_format

try:
    import memento_client
    from memento_client.memento_client import MementoClientException
except ImportError as e:
    memento_client = e


docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

ignorelist = [
    # Officially reserved for testing, documentation, etc. in
    # https://tools.ietf.org/html/rfc2606#page-2
    # top-level domains:
    re.compile(r'.*[\./@]test(/.*)?'),
    re.compile(r'.*[\./@]example(/.*)?'),
    re.compile(r'.*[\./@]invalid(/.*)?'),
    re.compile(r'.*[\./@]localhost(/.*)?'),
    # second-level domains:
    re.compile(r'.*[\./@]example\.com(/.*)?'),
    re.compile(r'.*[\./@]example\.net(/.*)?'),
    re.compile(r'.*[\./@]example\.org(/.*)?'),

    # Other special cases
    re.compile(r'.*[\./@]berlinonline\.de(/.*)?'),
    # above entry to be manually fixed per request at
    # [[de:Benutzer:BLueFiSH.as/BZ]]
    # bot can't handle their redirects:

    # bot rejected on the site, already archived
    re.compile(r'.*[\./@]web\.archive\.org(/.*)?'),
    re.compile(r'.*[\./@]archive\.is(/.*)?'),
    re.compile(r'.*[\./@]archive\.vn(/.*)?'),
    re.compile(r'.*[\./@]archive.li(/.*)?'),


    # ignore links to files like spreadsheets
    re.compile(r'.*[\./@]\.xlsx?(/.*)?'),
    re.compile(r'.*[\./@]\.docx?(/.*)?'),

    # ignore wikimedia projects links
    re.compile(r'.*[\./@]wikipedia\.org(/.*)?'),
    re.compile(r'.*[\./@]wiktionary\.org(/.*)?'),
    re.compile(r'.*[\./@]wikisource\.org(/.*)?'),
    re.compile(r'.*[\./@]wikimedia\.org(/.*)?'),


    # Ignore links containing * in domain name
    # as they are intentionally fake
    re.compile(r'https?\:\/\/\*(/.*)?'),

    # masti's collected exceptions
    re.compile('.*[\./@]anfp\.cl/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]antiqueadvertising\.com/pics/lucky\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bipraciborz\.pl/bip/dokumenty-akcja-wyszukaj-idkategorii-39906'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]brutalism\.com/content/anima-damnata-atrocious-disfigurement-of-the-redeemers-corpse-at-the-graveyard-of-humanity'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]brutalism\.com/content/hyperial-sceptical-vision'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]brutalism\.com/content/welicoruss-and-the-story-behind-skirts-and-make-up'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cavanheritage\.ie/Default\.aspx?StructureID_str=2'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ceausescu\.org/ceausescu_texts/revolution/trial-eng\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cityofandalusia\.com/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ck-czestochowa\.pl/wyszukiwarka-grobow/szukaj'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]ebelchatow\.pl/content/nie-plus-plus-polska-razem'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]europeanvoice\.com/folder/theswedishpresidencyoftheeu/124.aspx?artid=65305'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]federnuoto\.it/federazione/federazione-news/item/40079-barelli-eletto-alla-camera\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]forumakademickie\.pl/aktualnosci/2011/1/5/765/jak-ck-wybierano/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]forumakademickie\.pl/fa/2013/02/chalasinscy/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]forumakademickie\.pl/fa/2015/07-08/kronika-wydarzen/odzew-w-sprawie-bez-odzewu/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]gum\.gov\.pl/ftp'),  # bot rejected on site (masti, Akoshina)
    re.compile('.*[\./@]hej\.mielec\.pl/miasto2/repoe/art548,publiczne-gimnazjum-w-wadowicach-gornych-z-imieniem-leszka-deptuly-ten-dzien-zapisze-sie-w-historii\\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]jablunkov\.cz/ic/index\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]lameziainstrada\.com/politica/politiche-2018-matteo-salvini-eletto-senatore-in-calabria-furgiuele-deputato'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]linkedin\.com/in/krzysztof-lisek-7a6259bb/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]linyi\.gov\.cn/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]maius\.uj\.edu\.pl'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]monsourdelrosario\.com/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]movimentocinquestelle\.it/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]msp\.gov\.pl/pl/media/aktualnosci/31579,Zmiany-w-kierownictwie-MSP\\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]niccolorinaldi\.it/chi-sono/biografia\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]pip\.gov\.pl/pl/wiadomosci/69784,roman-giedrojc-glownym-inspektorem-pracy\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]pism\.pl/publications/bulletin/no-55-905'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]piw\.pl/indeks-autorow/ferry-luc'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]polishmusic\.ca/skok/cds/polskie/grupy/a/2plus1/2plus1\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]polishmusic\.ca/skok/cds/polskie/grupy/r/roma/roma\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]polishmusic\.ca/skok/cds/polskie/grupy/s/smerfy/smerfy\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]polishmusic\.ca/skok/cds/polskie/grupy/s/szczesni/szczesni\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rezeknesbiblioteka\.lv/index\.php?option=com_content&view=article&id=376:apsveicam-vladimirs-nikonovs&catid=163:par-izstadem-cb&Itemid=104'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]segodnya\.ua/politics/pnews/olga-bogomolec-sobiraetsya-ballotirovatsya-v-prezidenty-ukrainy-505598\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]shellenicparliament\.gr/en/Vouleftes/Diatelesantes-Vouleftes-Apo-Ti-Metapolitefsi-Os-Simera'),  # bot rejected on site (masti, Elfhelm)
# Ze słownikiem Kopalińskiego podobna sytuacja jak z Gcatholikiem, tzn\. część linków zgłoszona prawidłowo, część nieprawidłowo\. Nieprawidłowe zgłoszenia to:
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/02162EB3B37F6455412565B70004B0F9\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/0CE83B0EDC7B72F2C12565DB0064BCBF\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/18D2145DAFA7FBD3C12565BE001644D4\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/21BBD727783F862B412565CD0051A57E\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/246F68861BD49548412565BA003434EE\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/255DF08B813660F5412565BA0036F441\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/27192AAB9A0B2452412565B70039BB8A\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/27DC83AA85CAF6D5C125656F001C75B0\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/286890E66B322A6B412565BA0022F4CB\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/2D64302975D79C3AC125658C005F8974\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/2E48A299DC6EB482C125658B0074E140\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/2ED46894AB6C6A27C12565E70063258C\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/2FD5655E3C91FBCD412565D30056733A\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/2FFEDBF26AC72CCF412565B60051565A\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/33EF8940386A2E0AC12565EE005AE531\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/3BD9AF807D7613D2412565BA0022CCA0\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/3E3CFA773D4AABF3C12565BD006673CB\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/40650EF20C762479412565BF00294622\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/489E074C12B30A35412565CD004BECDB\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/4AB76064E593F011C125658C0063B83F\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/4AB9FF36C825C18FC125657C0081D067\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/4AD308518E458BA8412565B8001C110B\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/55ADB4D52C9A3ECBC12565BE0043D580\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/5774F597D0942D31412565CB0059A735\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/578F60BA759FF4A4412565BA002D82B8\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/650218F9F3D03517412565CB0072C82A\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/6DEC11B84950D1F9412565BA0021C94C\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/6FCBE3EE599F3EC3C12565B60006269D\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/7290491D99D06D0A412565D3004C6CD1\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/73D68C65F2C33E6BC12565BD003BCD92\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/7A9AECCA5EC4A591C12565BD0057FAD5\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/8061E4B2EE139D5AC12565EE006E6A0A\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/844BEF3539CCC370C12565EF0046B5C6\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/84C8DEF5AB6694F2412565CD005DB310\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/93E2A52FDA53B491C12565BD003B5FB3\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/944B03D3BB6696F6C12565BD00540FE8\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/97EC1A11607283AE412565CC004763B7\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/994E28BF6FC733A9412565BA00289ACA\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/9BB6A4284E15C4EEC12565E700674E8B\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/9CC69A2A9E99A48CC12565B5007CD020\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/ADE096011D04FB9DC12565BD0057383C\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/AE5ABDF9E893388EC12565EE005D855D\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/B9A4FD7AD8EC09F5412565BA002D5036\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/BB932EB1B605294A412565B80010EED6\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/C1489C254BDB29D1412565B800092026\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/C9CF9AFC8175D311412565CC007B6AE5\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/CEA41203C7084B3BC12565BE0039CDBC\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/D0EEBBD933631C13C12565D800472319\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/D14910AA76E13D8A412565D4004AEEE8\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/D6420FD8CDF9C6AF412565AF0078C733\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/DCC4BF7D21C6A5D3412565B8001B743A\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/DF34B55637518E1D412565B7003E98AD\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/E8B75264E4BDA91E412565CD004B610F\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/F9267F8EF0DE1437C12565DA00556B95\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]slownik-online\.pl/kopalinski/FB880FDFC5A8A9A0412565BD0035BFA4\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]songfacts\.com/detail\.php?id='),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]stowarzyszeniekongreskobiet\.pl/pl-PL/text/o_nas/rada_programowa'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]swr\.de/report/presse/-/id=1197424/nid=1197424/did=2918594/1wxuzhj/index\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]swr\.de/swraktuell/rp/ludwigshafen/entscheidung-in-ludwigshafen-spd-frau-jutta-steinruck-gewinnt-ob-wahl/-/id=1652/did=20434688/nid=1652/elild0/index\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]the-athenaeum\.org/art/by_artist\.php?Artist_ID=426'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]the-athenaeum\.org/art/detail\.php?ID= +wszystkie ID'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]the-athenaeum\.org/art/list\.php?m=a&s=tu&aid='),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]the-athenaeum\.org/art/list\.php?m=o&s=du&oid=1\.&f=a&fa=11380'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]the-athenaeum\.org/art/list\.php?m=o&s=du&oid=1\.&f=a&fa=3453'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]the-athenaeum\.org/art/list\.php?s=tu&m=a&aid=428&p=3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]the-athenaeum\.org/people/detail\.php?ID='),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ujfeherto\.hu/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]vaulnaveys-le-bas\.fr/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]vilalba\.gal/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]vilani\.lv/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]villefort-cevennes\.com/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]vismaskiclassics\.com/standings_total?personID=3421292'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]vysna-jedlova\.sk/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wloclawek\.info\.pl/nowosci,wiadomosci_wloclawek_i_region,1,1,tadeusz_dubicki_nowym_rektorem_p,16036\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]13grudnia81\.pl/portal/sw/wolnytekst/9499'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]13grudnia81\.pl/sw/wolnytekst/9499,dok\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]2lo\.traugutt\.net(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]academic\.oup\.com/aob/article-abstract/72/6/607/2769155'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]academic\.oup\.com/bioscience/article/53/4/421/250384'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]academic\.oup\.com/bioscience/article/57/3/227/268444'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]academic\.oup\.com/bioscience/article/62/1/67/295711'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]academic\.oup\.com/ijnp/article/15/6/825/761323'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]academic\.oup\.com/ijnp/article/18/11/pyv060/2910020]'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]academic\.oup\.com/ijnp/article/19/2/pyv076/2910032'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]academic\.oup\.com/ijnp/article/19/4/pyv124/2910122'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]academic\.oup\.com/jid/article/186/Supplement_1/S91/838964'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]actmedia\.eu/daily/cristian-diaconescu-was-appointment-as-foreign-affairs-minister/37811'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]aei\.org'),  # bot rejected on site (masti)
    re.compile('.*[\./@]age.ne\.jp/x/sas/96th_alljapan_j_nh-l2018results.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]age.ne\.jp/x/sas/96th_alljapan_j_nh-m2018results.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]age.ne\.jp/x/sas/alljapan_jump_lh_men_results20171105.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]age\.ne\.jp/x/sas'),  # bot rejected on site (masti, Snoflaxe)
    re.compile('.*[\./@]age\.ne\.jp/x/sas/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ak\.org\.pl/download/zywoty_swietych\.pdf(/.*)?'),  # well known missing doc  (masti)
    re.compile('.*[\./@]allaboutmusic\.pl'),  # bot rejected on site (masti, edk)
    re.compile('.*[\./@]allafrica\.com(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]allmusic\.com/album/r146898'),  # bot rejected on site (masti, Janusz61)
    re.compile('.*[\./@]alpha\.bn\.org\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]americanskijumping\.com/hof\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]amt-franzburg-richtenberg\.de'),  # bot rejected on site (masti)
    re.compile('.*[\./@]amt-jarmen-tutow\.de'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]annalubanska\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]anonimagroup\.org/index\.php'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]anst.gov\.ro/documente/documente/0993-1016%20National%20Federations%20-%20Ski%20-%20Biathlon%20.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]antibr\.ru'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]antiqueadvertising\.com/price-guide/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]apa\.org'),  # redirect loop (masti)
    re.compile('.*[\./@]archinea\.pl/biblioteka-uniwersytetu-warszawskiego-marek-budzynski-zbigniew-badowski/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]archinea\.pl/sad-najwyzszy-w-warszawie-marek-budzynski-zbigniew-badowski/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]archinform\.net'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]architektura\.um\.warszawa\.pl/ekofizjografia-zakola-wawerskiego'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]architektura\.um\.warszawa\.pl/ekofizjografia'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]architektura\.um\.warszawa\.pl/hydrografia'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]architektura\.um\.warszawa\.pl/plany_uchwalone_ochota]'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]architektura\.um\.warszawa\.pl/sites/default/files/files/Ekofizjografia_tekst\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]architektura\.um\.warszawa\.pl/sites/default/files/files/Zakole_Wawerskie_1_wstep_1\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]architektura\.um\.warszawa\.pl/sites/default/files/files/Zakole_Wawerskie_2\.1_geologia_0\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]architektura\.um\.warszawa\.pl/sites/default/files/files/Zakole_Wawerskie_2\.4_wody\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]architektura\.um\.warszawa\.pl/sites/default/files/files/Zakole_Wawerskie_2\.5-2\.7_gleby_roslinnosc_fauna\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]architektura\.um\.warszawa\.pl/wisla'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]archive\.fo'),  # redirect t archive.is (masti)
    re.compile('.*[\./@]archive\.is(/.*)?'),  # bot rejected on the site (masti)
    re.compile('.*[\./@]archive\.org(/.*)?'),  # bot rejected on the site (masti)
    re.compile('.*[\./@]archive\.today(/.*)?'),  # bot rejected on the site  (masti)
    re.compile('.*[\./@]arquidiocesisdesucre\.org\.bo'),  # bot rejected on site (masti)
    re.compile('.*[\./@]artrenewal\.org/pages/artist\.php?artistid=1857&page=1'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]artrenewal\.org/pages/artist\.php?artistid=305&page=1'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]artrenewal\.org/pages/artist\.php?artistid=5317&page=1'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]astronomynow\.com/news'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]atlaspsow\.online'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]atlasryb\.online/opis_ryby.php?id= (wszystkie numery po "id")'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]atlasryb\.online/opis_ryby\.php\?id='),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]auerbach-erzgebirge\.de'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]automobile-catalog\.com(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]automobile-catalog\.com(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]bank\.gov\.ua/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]basketball-players\.pointafter\.com(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]bbc\.co\.uk/radio3/world/onyourstreet/dholhistory.shtml '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]berlinonline\.de(/.*)?'),  # a de: user wants to fix them by hand and doesn't want them to be deleted, see [[de:Benutzer:BLueFiSH.as/BZ]].
    re.compile('.*[\./@]biancofiore\.pl '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]biblioteka\.nama-hatta\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]biblioteka\.zagorz\.pl/texts/view/2'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bielskpodlaski\.pl/asp/pl_start\.asp?typ=14&sub=3&menu=15&strona=1'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]bielskpodlaski\.pl/asp/pl_start\.asp?typ=14&sub=3&menu=15&strona=1'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]bielskpodlaski\.pl/asp/pl_start\.asp?typ=14&sub=3&menu=15&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bielskpodlaski\.pl/asp/pl_start\.asp\?typ=14&sub=3&menu=15&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bielskpodlaski\.pl/asp/pl_start\.asp\?typ=14&sub=3&menu=15&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bierutow\.pl/asp/pl_start\.asp\?typ=14&menu=28&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bilkent\.edu\.tr/bilkent/bilkent-mourns-the-loss-of-janusz-szprot-former-instructor-at-the-faculty-of-music-and-performing-arts'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]biodiversitylibrary\.org'),  # bot rejected on site (masti)
    re.compile('.*[\./@]bip\.bytow\.com\.pl/m,420,solectwa\.html'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]bip\.czersk\.pl/2112\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bip\.gminaolawa\.pl/Article/get/id,14856\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bip\.gminastarytarg\.pl/archiwum/www\.bip\.gminastarytarg\.pl/userfiles/PONZ%20Stary%20Targ%20binarny_na%20lata%202016_2019_AKTUALIZACJA\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bip\.jaworzno\.pl/Article/id,18060\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]bip\.mazovia\.pl/samorzad/zarzad/uchwaly-zarzadu/uchwala,40669,15948319\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]bip\.miekinia\.pl/Article/get/id,17673\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bip\.powiatboleslawiecki\.pl/oswiadczenia'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]bip\.sobkow\.pl/\?bip=1&cid=51&bsc=N'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bip\.umwp\.wrotapodlasia\.pl/wojewodztwo/oswiadczenia/oswiad_majo/oswiadczenia_majatkowe_od_2009/oswiadczenie-majatkowe-anna-naszkiewicz-4\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]biuletyn\.net/nt-bin/_private/biskupiec/1209\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]biuletyn\.net/nt-bin/_private/dubiecko/3618\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]biuletyn\.net/nt-bin/_private/radomysl/8911\.pdf'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]biuletyn\.net/nt-bin/start\.asp?podmiot=kazimierzawielka/&strona=14&typ=podmenu&menu=128&id=170&str=8'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]biuletyn\.net/nt-bin/start\.asp?podmiot=kazimierzawielka/&strona=14&typ=submenu&typmenu=14&id=135&str=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]biuletyn\.net/nt-bin/start\.asp?podmiot=kazimierzawielka/&strona=14&typ=submenu&typmenu=14&id=228&str=5'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]biuletyn\.net/nt-bin/start\.asp?podmiot=zaklikow/&strona=14&typ=podmenu&typmenu=14&menu=7&id=31&str=1'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]biuletyn\.net/nt-bin/start\.asp\?podmiot=wartkowice/&strona=14&typ=podmenu&typmenu=14&menu=34&id=34&str=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]blasonariosubalpino\.it'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bobruisk\.hram\.by'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bodo\.kommune\.no(/.*)?'),  # bot can't handle their redirects
    re.compile('.*[\./@]boxrec\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]bpi.co.uk/award/ - wszystkie podstrony'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bpi\.co\.uk/bpi-awards/'),  # bot rejected on site (masti)
    re.compile('.*[\./@]bpi\.co\.uk/brit-certified/'),  # bot rejected on site (masti)
    re.compile('.*[\./@]britannica\.com(/.*)?'),  # HTTP redirect loop
    re.compile('.*[\./@]brzostek\.pl/asp/pl_start\.asp?typ=14&menu=289&strona=1&sub=278#strona'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]brzostek\.pl/asp/pl_start\.asp\?typ=14&menu=289&strona=1&sub=278'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]bs\.sejm\.gov\.pl'),  # slow response (masti)
    re.compile('.*[\./@]cafonline\.com/en-us/competitions/31theditionofafricancupofnationtotal,gabon2017'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-us/competitions/32ndeditionoftotalafricacupofnations'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-us/competitions/32ndeditionoftotalafricacupofnations/MatchDetails?MatchId=c8WFJCFnBOuM7mR%2feYEFkCmdq3y59q4uIqqQwH7I4XBdCUMKpVuT5gHSHovlxfKL'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-us/competitions/africanwomenchampionship,cameroon2016'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-us/competitions/allafricagamesmencongo2015'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-us/competitions/orangeafricacupofnations,equatorialguinea2015.aspx'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-us/competitions/orangeafricacupofnations,equatorialguinea2015'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-us/competitions/qcan2017.aspx'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-us/competitions/qcan2017'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-us/competitions/tn9thafricanwomenchampionship-namibia/news.aspx/NewsDetails?id=FiwOlHoESQWLBCXDsqhA7w%3D%3D'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-us/memberassociations/f%C3%A9d%C3%A9rationgabonaisedefootball'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-US/NewsCenter/News/NewsDetails?id=7hxNqK1bVNLnCtOlOfU1ZA%3D%3D'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-US/NewsCenter/News/NewsDetails?id=7Q1Us%2BTZ%2Bi03aalfg76fmw%3D%3D'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-US/NewsCenter/News/NewsDetails?id=8OD0yxG/y9dts7Ih8e/JqA%3D%3D'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-US/NewsCenter/News/NewsDetails?id=auMqtAj3SdstqcMlrNnjPQ%3D%3D'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-US/NewsCenter/News/NewsDetails?id=KXDfhHRQfmo848MmjaimQA%3D%3D'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-US/NewsCenter/News/NewsDetails?id=PEhc3UzJyA5sc0oWvJWcag%3D%3D'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-US/NewsCenter/News/NewsDetails?id=rHQkXwbJ/qnlkT0kYVKcMg%3D%3D'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-US/NewsCenter/News/NewsDetails?id=tjUi4YBkLWPBNKHA%2B7kBJg%3D%3D'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/en-US/NewsCenter/News/NewsDetails?id=vHiSLG/k2NKtlLQi4VfGCA%3D%3D'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/Portals/0/glo%20caf%202014/Draw%20Procedure%20-%20FT%20AFCON%202017%20---.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/Portals/0/glo%20caf%202014/Final%20Ranking%20AFCON%20FT,%20Gabon%202017%20FT%20FT.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/Portals/0/President/ranking%20tirage%20PDF%20English.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/Portals/0/President/ranking%20tirage%20PDF%20English.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/Portals/0/Total%20AFCON%202016/Qualifiers%20CAN%202019%20-%20matches.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\.com/Portals/0/Total%20AFCON%202016/Qualifiers%20CAN%202019%20-%20matches.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cafonline\\.com/en-us/competitions/32ndeditionoftotalafricacupofnations/MatchDetails?MatchId=c8WFJCFnBOuM7mR%2feYEFkCmdq3y59q4uIqqQwH7I4XBdCUMKpVuT5gHSHovlxfKL'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]canadianpoetry\.org/2016/06/28/widow-of-the-rock/#thewidowoftherock'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]canicattiweb\.com/2009/05/18/nuovo-cda-della-banca-san-francesco-di-canicatti/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]canmore\.org\.uk'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]canna\.pl/tuszyn/index\.php\?page=historia_kalendarium'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cantat\.amu\.edu\.pl:80/pl/universitas-cantat-2015/konkurs-kompozytorski-na-dzielo-finalowe '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]carfolio\.com(/.*)?'),  # site very slow timeouts  (masti)
    re.compile('.*[\./@]cars\.com/articles/lamborghini-urus-concept-at-the-beijing-motor-show-1420663120980/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]catholic-hierarchy\.org/'),  # bot rejected on site (masti)
    re.compile('.*[\./@]catholic-hierarchy\.org/bishop'),  # bot rejected on site (masti)
    re.compile('.*[\./@]catholic-hierarchy\.org/diocese'),  # bot rejected on site (masti)
    re.compile('.*[\./@]caudetedelasfuentes\.es'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]cbc\.ca/news/entertainment/vancouver-actor-nabs-csi-role-1\.680212'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cbc\.ca/sports/olympics-winter/1956-cortina-d-ampezzo-italy-1\.864041'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cbc\.ca/world/story/2006/06/07/france-pay\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cbssy.sy/new%20web%20site/General_census/census_2004/NH/'),  # bot rejected on site (masti)
    re.compile('.*[\./@]ceciliabartolionline\.com '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]census\.gov(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]cev\.lu(/.*)?'),  # bot rejected on the site
    re.compile('.*[\./@]chor\.umed\.wroc\.pl '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]chybie\.pl/asp/pl_start\.asp\?typ=14&sub=2&menu=4&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ciaaw\.org/atomic-weights\.htm'),  # bot rejected on site (masti, CiaPan)
    re.compile('.*[\./@]cieplodlatrojmiasta\.pl/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cityofshoreacres.us'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ck-czestochowa\.pl/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]climatebase\.ru/station'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]clubz\.bg/4341-kogo_prashtame_v_evropejskiq_parlament'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cmi2\.yale\.edu/ym/archive/artists/jamespeale/artist\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]coiu\.pl/media/download/Obywatelskie_inicjatywy_ustawodawcze_Solidarnosci_1980-1990\.pdf'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]comune\.sora\.fr\.it'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]concertorganists\.com/site2009/artist2\.aspx?id=67'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]contraloria\.gob\.pa'),  # bot rejected on site (masti)
    re.compile('.*[\./@]cotes\.es/'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]cruxgaliciae\.org'),  # bot rejected on site (masti)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vnd2006/w6p001\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vnd2007/w6p001\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vnd2012/wp001\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vnd2012/wp001\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vnd2012/wp001\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vnd2014/wp001\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vnd2014/wp001\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vnd2014/wp001\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vnd2019/wp001\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vnd2019/wp001\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vp2014/wp001\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vp2014/wp001\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]cvk\.gov\.ua/pls/vp2019/wp001\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]czd\.pl/index\.php\?option=com_content&view=article&id=3131:koncert-podsumowujcy-obchody-40-lecia-ipczd&catid=27:wane&Itemid=420'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]czyczy\.pl/2012/jadrowa/litwa-energetyka-jadrowa-polegla-w-referendum'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]czyczy\.pl/2014/jadrowa/wlk-brytania-sellafield-troche-rzeczywistych-danych-kosztach-rozbiorki-elektrowni-jadrowej'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]czyczy\.pl/mapa'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]d-nb\.info(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]da\.katowice\.pl/lux-ex-silesia'),  # bot rejected on site (masti)
    re.compile('.*[\./@]daniiltrifonov\.com '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]db\.ipc-services\.org/sdms/hira/web/competition/code/PG1994'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]db\.ipc-services\.org/sdms/hira/web/country/code'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]delibra\.bg\.polsl\.pl/Content/24007/BCPS_25841_1927_Polskie-Towarzystwo-\.pdf'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]delibra\.bg\.polsl\.pl/Content/25374/BCPS_28917_1927_Podrecznik-inzyniers\.pdf'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]delipark\.pl'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]demografia\.stat\.gov\.pl/bazademografia/Tables\.aspx'),  # bot rejected on site (masti)
    re.compile('.*[\./@]demographia\.com/db-worldua.pdf(/.*)?'),  # well known missing doc  (masti)
    re.compile('.*[\./@]deon\.pl(/.*)?'),  # bot rejected on the site  (masti)
    re.compile('.*[\./@]depatisnet\.dpma\.de(/.*)?'),  # bot rejected on the site  (masti)
    re.compile('.*[\./@]deu\.archinform\.net'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]diecezja\.rzeszow\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]diecezja\.wloclawek\.pl'),  # bot rejected on site (masti, Wiktoryn)
    re.compile('.*[\./@]dioceseofscranton\.org'),  # bot rejected on site (masti)
    re.compile('.*[\./@]discogs\.com(/.*)?'),  # bot rejected on the site  (masti)
    re.compile('.*[\./@]dlastudenta\.pl(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]dlastudenta\.pl(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]dlibra\.bg\.ajd\.czest\.pl:8080/Content/855/Kultura_fizyczna_9\.-57\.pdf'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]dlibra\.umcs\.lublin\.pl/dlibra/plain-content?id=3251'),  # bot rejected on site (masti)
    re.compile('.*[\./@]dlibra\.umcs\.lublin\.pl/dlibra/plain-content\?id=3251'),  # bot rejected on site (masti)
    re.compile('.*[\./@]doi\.org'),  # false positive (masti)
    re.compile('.*[\./@]dovidka\.com\.ua'),  # bot rejected on site (masti)
    re.compile('.*[\./@]dre\.pt/application/dir/pdf1sdip/2013/01/01901/0000200147\.pdf'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]dre\.pt/pdf2sdip/2009/02/040000000/0769107691\.pdf'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]drelow\.pl/asp/pl_start\.asp\?typ=14&sub=2&menu=20&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]dsm.psychiatryonline\.org//book.aspx?bookid=22'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]duwo\.opole\.uw\.gov\.pl/WDU_O/2019/1695/akt\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]dzieje\.pl(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]dzieje\.pl(/.*)?'),  # bot rejected on the site  (masti)
    re.compile('.*[\./@]dziennikustaw\.gov\.pl/DU'),  # bot rejected on site (masti)    http://dziennikustaw.gov.pl/du
    re.compile('.*[\./@]dziennikustaw\.gov\.pl/du'),  # bot rejected on site (masti)    http://dziennikustaw.gov.pl/du
    re.compile('.*[\./@]dziennikzbrojny\.pl/aktualnosci/news,1,2155,aktualnosci-z-polski,robert-kupiecki-wiceministrem-on'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]earlparkindiana\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]eco\.gov\.az/en/67-hydrometeorology'),  # bot rejected on site (masti)
    re.compile('.*[\./@]edziennik\.poznan\.uw\.gov\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]eksploratorzy\.com\.pl/viewtopic\.php?p=153649#p153649'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]elk\.gmina\.pl/nauczmy-sie-na-pamiec-tego-kraju-gminne-obchody-2-i-3-maja'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]emmelle\.it'),  # bot rejected on site (masti)
    re.compile('.*[\./@]emporis\.com/buildings'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]emporis\.com/city'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]emporis\.com/complex/100329/world-trade-center-new-york-city-ny-usa'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]emporis\.com/statistics/tallest-buildings/country/100156/spain'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]encyklopedia\.pwn\.pl/haslo/sredniowiecze-Muzyka;4019677.html '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]encysol\.pl'),  # wrong URLs (masti)
    re.compile('.*[\./@]entsyklopeedia\.ee'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]eosielsko\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]epolotsk\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]erc24\.com/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]erc24\.com/archives/16292'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]eredivisiestats\.nl/topscorers.php'),  # bot rejected on site (masti)
    re.compile('.*[\./@]esbl\.ee/biograafia'),  # bot rejected on site (masti)
    re.compile('.*[\./@]ethnologue\.com/country/CF'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ethnologue\.com/country/CL'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ethnologue\.com/language/[a-z]{3}'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ethnologue\.com/subgroups/australian'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ethnologue\.com/subgroups/b2-1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ethnologue\.com/subgroups/germanic'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ethnologue\.com/subgroups/tangale'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]euroferroviarios\.net'),  # bot rejected on site (masti)
    re.compile('.*[\./@]europarl\.europa\.eu/meps(/.*)?'),  # links redirected  (masti)
    re.compile('.*[\./@]europe-politique\.eu'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]europe-politique\.eu/union-pour-l-europe\.htm'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]europeanvoice\.com/folder/theswedishpresidencyoftheeu/124\.aspx\?artid=65305'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]ewrc-results\.com/season/\d{4}/6-erc'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]fcgoverla\.uz\.ua/index\.php\?page=history'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]fenditton\.org'),  # bot rejected on site (masti)
    re.compile('.*[\./@]file\.scirp\.org/Html'),  # bot rejected on site (masti, Wiklol)
    re.compile('.*[\./@]flutopedia\.com'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]flutopedia\.com/ '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]formula3\.co'),  # bot rejected on site (masti)
    re.compile('.*[\./@]forumakademickie\.pl/fa/2013/02/chalasinscy'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]fra\.archinform\.net'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]frazettaartmuseum\.com'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]frontnational\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]ft\.dk(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]galeriabwa.bydgoszcz\.pl/wystawa/milosz-matwijewicz-moj-malowany-swiat'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]galewice\.pl/asp/pliki/Gmina_Galewice/Charakterystyka_gminy_Galewice\.pdf'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gamespot\.com(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]gazeta-mlawska\.pl/aktualnosc-2186-wybory_do_rady_powiatu_mlawskiego__psl_ma_wiekszosc_\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]gazetagazeta\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]gazetapolska\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]gcatholic\.org/dioceses/conference/018\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/country'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/country/AR-province\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/country/CN\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/country/CR-province\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/country/CU-province\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/country/IE\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/country/PY-province\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/country/SS\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/country/UA-province\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/data/rite-Rt\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/agan0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/algi0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/amad0\.htm#3222'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/amma0\.htm '),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/angr0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/angr0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/anta0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/anti0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/anto0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/antw0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/areq0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/ayac0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/bang2\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/bans0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/barq0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/barr0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/bele0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/bere0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/bogo0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/buca0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/cala1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/caph0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/cara0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/caro1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/cart0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/casc0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/cast0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/celj0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/chan0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/cili0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/ciud0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/coch0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/coro0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/cuma0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/curi0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/cuzc0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/cypr0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/done0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/falk0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/falk0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/funa0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/goaa0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/goaa0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/guay0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/hany0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/hels0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/honi0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/honi0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/huan0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/ibag0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/ivan0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/king1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/koln0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/koln0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/kolo0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/kyrg0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/lase0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/lisb0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/lisb0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/ljub0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/ljub0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/loya0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/luts0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/luts0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/luts1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/lviv1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/lviv1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/maca1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/malt0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/mani0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/mani1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/mara0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/mars2\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/mars2\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/melf0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/meri0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/moun0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/muka0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/nass0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/ndja0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/ndja0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/neth0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/neth0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/nico0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/npam0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/odes1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/pana0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/pape0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/pari2\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/paup0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/phil1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/phno0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/pmor0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/popa0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/port0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/priz0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/priz0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/priz0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/pvil0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/pyon0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/pyon0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/quit0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/raba0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/raro0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/rome0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/soka0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/sucr0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/suva0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/taio0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/taio0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/tara2\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/tern1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/tong0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/tong0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/truj0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/tsin0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/tuba0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/tunj0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/utre0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/vale1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/vill3\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/viln0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/wall0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/wanh0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/winn0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/wloc0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/yamo0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/yamo0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/yoko0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/yung3\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/zcru0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/zdom0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/zfed0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/zjos7\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/zjua1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/zpau0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/ztia1\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/ztia3\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0136\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0895\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1090\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1091\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1093\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1094\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1095\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1108\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1109\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1110\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1111\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1113\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1686\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t2060\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/vlad0\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/nunciature/nunc034\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/nunciature/org220\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/organizations/card\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-MAS\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-ST\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-X\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/cardL13-5\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/officials-B\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/officials-M\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/pope/G13\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/orders/018\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/orders/019\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/orders/053\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/orders/index\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gcatholic\.org/toronto/pr-we\.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]genealogics\.org/getperson\.php'),  # bot rejected on site (masti)
    re.compile('.*[\./@]geojournals\.pgi\.gov\.pl/agp/article/view'),  # bot rejected on site (masti, Wiklol)
    re.compile('.*[\./@]geojournals\.pgi\.gov\.pl/pg/article/viewFile/16266/13503'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]geojournals\.pgi\.gov\.pl/pg/article/viewFile/16266/13503'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]geonames\.usgs\.gov(/.*)?'),  # site very slow timeouts  (masti)
    re.compile('.*[\./@]geoportal\.cuzk\.cz/mapycuzk'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]get-ligaen\.stats\.pointstreak\.com/scoreboard.html'),  # bot rejected on site (masti)
    re.compile('.*[\./@]gimnazjum\.bystrzyca\.eu'),  # bot rejected on site (masti)
    re.compile('.*[\./@]glencteresa.pl/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]gminaczarna\.pl/asp/pliki/download/statystyka_ludnosci_31-12-2017\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gminajozefow\.pl/soltysi-2/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gminajozefow\.pl/wyniki-konsultacji-spolecznych/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gminajozefow\.pl/zapraszamy-do-udzialu-w-konsultacjach-spolecznych/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gminajozefow\.pl/zawiadomienie-o-sesji-rady-gminy-2/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gminalancut\.pl/asp/pl_start\.asp\?typ=14&menu=28&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gminalancut\.pl/asp/pl_start\.asp\?typ=14&menu=475&strona=1&sub=425'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gminalancut\.pl/asp/pl_start\.asp\?typ=14&menu=87&strona=1&prywatnosc=tak'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gminalancut\.pl/asp/pl_start\.asp\?typ=14&menu=93&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gminawilkow\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]gniezno\.eu/cms/20189/nagroda_kulturalna_miasta_gniezna'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gniezno\.eu/cms/20276/miasto_w_liczbach'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gniezno\.eu/cms/20285/ambasadorzy'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gniezno\.eu/cms/20542/vii_pustachowakokoszki_'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gniezno\.eu/cms/25147/trakt_krolewski_w_gnieznie'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gniezno\.eu/katalog/2290/szkola_podstawowa__nr_1_im_zjazdu_gnieznienskiego'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gniezno\.eu/wiadomosci/1/wiadomosc/111630/projekty_22_nowych_posagow_wybrane'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gniezno\.eu/wiadomosci/1/wiadomosc/126702/trakt_krolewski_w_ostatnim_etapie_realizacji'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]goranbregovic\.co\.rs '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]gorzowianin\.com/wiadomosc/10529-tvp-wybuduje-w-koncu-siedzibe\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gorzowianin\.com/wiadomosc/10584-zamiast-kary-dwa-nowe-linki\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gorzowianin\.com/wiadomosc/11301-powstanie-przystanek-kolejowy-gorzow-zachod-zdjecia\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gorzowianin\.com/wiadomosc/7775-radio-go-juz-ruszylo-w-rytmie-hitow-tylko-na-1017-fm\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gorzowianin\.com/wiadomosc/9607-z-centrum-na-zawarcie-to-bedzie-wielki-korek\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gorzowianin\.com/wiadomosc/9746-pociag-do-berlina-coraz-bardziej-popularny\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]granowo\.pl/asp/pl_start\.asp?typ=14&sub=14&menu=114&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]granowo\.pl/asp/pl_start\.asp?typ=14&sub=14&menu=29&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]granowo\.pl/asp/pl_start\.asp?typ=14&sub=14&menu=30&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]granowo\.pl/asp/pl_start\.asp\?typ=14&sub=14&menu=114&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]grapplerinfo\.pl/amatorski-puchar-ksw'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]greghancock\.com'),  # bot rejected on site (masti, Klima)
    re.compile('.*[\./@]grodziczno\.pl/asp/pl_start\.asp?typ=14&sub=12&menu=26&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]grodziczno\.pl/asp/pl_start\.asp\?typ=14&sub=12&menu=26&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]grodziczno\.pl/asp/pl_start\.asp\?typ=14&sub=12&menu=26&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]groupofsevenart\.com/ '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]gryfice\.eu/gryfice\.eu-strona-archiwalna/zabytki\.html'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gsemilia\.it/index\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]gso\.gbv\.de(/.*)?'),  # bot somehow can't handle their redirects
    re.compile('.*[\./@]gutenberg\.org(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]gwz.bielsko\.pl'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]halama\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]hanba1926\.pl '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]harku\.ee'),  # bot rejected on site (masti)
    re.compile('.*[\./@]heilsbronn\.de(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]heimenkirch\.de(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]heraldry\.com\.ua/index\.php3?lang=U&context=info&id=920'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]hertfordshiremercury\.co\.uk'),  # bot rejected on site (masti)
    re.compile('.*[\./@]hfhr\.org\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]hfhrpol\.waw\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]hipic\.jp '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]historialomzy\.pl/orzel-kolno/'),  # bot rejected on site (masti)
    re.compile('.*[\./@]history\.house\.gov/Institution/Party-Divisions/Party-Divisions'),  # (masti, Ptjackyll)
    re.compile('.*[\./@]historyofpainters\.com/ralph_blakelock\.htm'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]histpol.pl.ua/ru/biblioteka/ukazatel-po-nazvaniyam?id=491'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]histpol.pl.ua/ru/gosudarstvennoe-upravlenie/sudebnye-i-pravookhranitelnye-organy-pravo?id=1759'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]histpol.pl.ua/ru/kultura/pechatnye-izdaniya/gazety?id=2366'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]horneburg\.de'),  # bot rejected on site (masti)
    re.compile('.*[\./@]horodlo\.pl/asp/pl_start\.asp\?typ=14&menu=22&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]horodlo\.pl/asp/pl_start\.asp\?typ=14&menu=24&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]hrubieszow-gmina\.pl/gmina/solectwa-soltysi'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]ibdb\.com(/.*)?'),  # redirect  (masti)
    re.compile('.*[\./@]ibiblio\.org/lighthouse/tallest\.htm ten'),  # bot rejected on site (masti, Janusz61)
    re.compile('.*[\./@]iep\.utm\.edu'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]ifpicr\.cz'),  # false positive (masti)
    re.compile('.*[\./@]inafed\.gob\.mx/work/enciclopedia/EMM27tabasco/index\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]independent\.co\.uk'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]independent\.co\.uk'),  # bot rejected on site (masti, Wikipek)
    re.compile('.*[\./@]independent\.ie(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]inews\.co\.uk/news/politics/who-my-mp-won-constituency-area-general-election-2019-results-full-list-mps-1340769'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]inserbia\.info'),  # bot rejected on site (masti)
    re.compile('.*[\./@]insidehoops\.com/blog/?p='),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]interlude\.hk'),  # timeouts (masti)
    re.compile('.*[\./@]ipn\.gov\.pl/pl/aktualnosci/44090,Uroczystosc-wreczenia-odznaczen-panstwowych-Warszawa-13-grudnia-2017\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]ira\.art\.pl'),  # false positive (masti)
    re.compile('.*[\./@]irishcharts\.ie/search/placement'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]itis\.gov(/.*)?'),  # bot rejected on the site
    re.compile('.*[\./@]iz\.poznan\.pl/aktualnosci/wydarzenia/nowa-rada-instytutu-zachodniego'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]iz\.poznan\.pl/aktualnosci/wydarzenia/nowa-rada-instytutu-zachodniego'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]jamanetwork\.com/journals/archneurpsyc/article-abstract/642767'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]jamanetwork\.com/journals/jama/fullarticle/1104423'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]jamanetwork\.com/journals/jama/fullarticle/198487'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]jamanetwork\.com/journals/jamaotolaryngology/article-abstract/2681628?widget=personalizedcontent&previousarticle=2685259'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]jamanetwork\.com/journals/jamapsychiatry/article-abstract/209616'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]jamanetwork\.com/journals/jamapsychiatry/fullarticle/2517515'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]jamanetwork\.com/journals/jamapsychiatry/fullarticle/2599177'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]jamanetwork\.com/journals/jamapsychiatry/fullarticle/2604310'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]jaskinia\.pl/jaskinia_pl\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]jedlnia\.biuletyn\.net/\?bip=1&cid=1155'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]jerzymalecki\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]jezowe\.biuletyn\.net/?bip=1&cid=143'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]journals\.indexcopernicus\.com'),  # slow site (masti)
    re.compile('.*[\./@]journals\.indexcopernicus\.com/search/details\?id=16423'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]journals\.indexcopernicus\.com/search/details\?id=3495'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]jpl\.nasa\.gov(/.*)?'),  # bot rejected on the site
    re.compile('.*[\./@]jura-pilica\.com/?rezerwat-ruskie-gory-,388'),  # bot rejected on site (masti)
    re.compile('.*[\./@]jusbrasil\.com\.br'),  # bot rejected on site (masti)
    re.compile('.*[\./@]justallstar\.com/contests/discontinued/legends'),  # bot rejected on site (masti, B-X)
    re.compile('.*[\./@]justallstar\.com/nba-all-star-game/coaches'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]juwra\.com'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]kadra\.pl(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]kameralisci\.pl/ '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]kanalbydgoski\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]karczew\.pl/asp/pl_start\.asp?typ=14&menu=89&strona=1&sub=21&subsub=32'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]karlovaves\.sk/samosprava/starostka/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]katalog\.bip\.ipn\.gov\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]keanemusic\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]kedzierzynkozle\.pl/portal/index\.php\?t=200&id=35673'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]kelseyserwa\.com'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]kettererkunst\.com/bio/LyonelFeininger-1871-1956\.shtml'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]kinakh\.com\.ua/bio'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]kloczew\.eurzad\.eu'),  # bot rejected on site (masti)
    re.compile('.*[\./@]koeppen-geiger\.vu-wien\.ac\.at/'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]kolejpiaskowa\.pl/index\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]kopernik\.net\.pl/imprezy-i-festiwale/swietojanski-festiwal-organowy '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]kosmonauta\.net'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]krakowskascenamuzyczna\.pl/artykuly/the-toobes-dla-nich-najwazniejsza-jest-komercja-wywiad'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]krakowskascenamuzyczna\.pl/zespoly/hanba/ '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]krknews\.pl/zobaczyc-caly-swiat-swietna-akcja-krakowem-barany-wytepione-ruchu-wideo/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]krs-online\.com\.pl(/.*)?'),  # bot rejected on the site  (masti)
    re.compile('.*[\./@]ksi.home\.pl/archiwaprzelomu/obrazy/AP-6-1-1-42_23\.PDF'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]ksi.home\.pl/archiwaprzelomu/obrazy/AP-6-1-1-44_39\.PDF'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]ksi.home\.pl/archiwaprzelomu/obrazy/AP-6-1-1-44_40\.PDF'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]kszosiatkowka\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]kulturalna\.warszawa\.pl/kapuscinski,1,2794\.html\?locale=pl_PL'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]kulturalna\.warszawa\.pl/osoby,1,11053,0,Mindaugas_Kvietkauskas\.html\?locale=pl_PL'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]kuriergalicyjski\.com/actualnosci/polska/1487-adam-rotfeld-we-lwowie\?showall=1&limitstart='),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]kuriergalicyjski\.com/actualnosci/report/6631-nagroda-specjalna-ministra-kultury-i-dziedzictwa-narodowego-rp-dla-kuriera-galicyjskiego'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]kuriergalicyjski\.com/historia/zabytki/3123-tajna-apteka'),  # bot rejected on site (masti)
    re.compile('.*[\./@]kuriergalicyjski\.com/kultura/film/7201-produkcja-kuriera-galicyjskiego-wyrozniona-na-vi-festiwalu-filmowym-emigra'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]kyivpost\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]lallameryemtennis\.com'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]lazarus\.elte\.hu/hun/digkonyv/topo/3felmeres\.htm'),  # bot rejected on site (masti)
    re.compile('.*[\./@]lazarz\.pl'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]lead\.org\.au/lanv1n2/lanv1n2-8\.html'),  # bot rejected on site (masti, CiaPan)
    re.compile('.*[\./@]leparisien\.fr'),  # bot rejected on site (masti)
    re.compile('.*[\./@]leyendablanca\.galeon\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]liceum1\.bystrzyca\.eu'),  # bot rejected on site (masti)
    re.compile('.*[\./@]lietuvosdiena\.lrytas\.lt/aktualijos/seimo-pirmininku-isrinktas-viktoras-pranckietis-20161114033033\.htm'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]ligocka\.wydawnictwoliterackie\.pl'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]listaptakow\.eko\.uj\.edu\.pl/nonpasserines1\.html'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]listaptakow\.eko\.uj\.edu\.pl/passerines1\.html'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]listaptakow\.eko\.uj\.edu\.pl/passerines2\.html'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]lobzenica\.pl/asp/pl_start\.asp?typ=14&menu=10&strona=1&sub=139&subsub=141&subsubsub=142'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]lobzenica\.pl/asp/pl_start\.asp\?typ=14&menu=10&strona=1&sub=139&subsub=141&subsubsub=142'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]lobzenica\.pl/asp/pl_start\.asp\?typ=14&menu=10&strona=1&sub=139&subsub=141&subsubsub=142'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]lowell\.edu/staff-member/emeritus-astronomers'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]lrs\.lt/datos/kovo11/signatarai/www_lrs\.signataras-p_asm_id=8\.htm'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]lrs\.lt/sip/portal\.show\?p_r=119&p_k=1&p_t=167698'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]lrs\.lt/sip/portal\.show\?p_r=35299&p_k=1&p_a=498&p_asm_id=47839'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]mae\.ro'),  # bot rejected on site (masti)
    re.compile('.*[\./@]majdankrolewski\.pl/asp/pl_start\.asp\?typ=14&menu=6&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]mandolinluthier\.com'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]mapy\.zabytek\.gov\.pl/nid'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]mareksierocki\.com'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]matica\.hr/knjige/autor/576/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]matriculasdelmundo\.com/gibraltar\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]mazovia\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]media\.metro\.net/riding_metro/bus_overview/images/803\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]metacritic\.com'),  # false positive (masti)
    re.compile('.*[\./@]metro\.gov\.az'),  # bot rejected on site (masti)
    re.compile('.*[\./@]michal_wasilewicz\.users\.sggw\.pl/Inz_rzeczna/wyklady/Wyklad_9\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]miedzyrzecgmina\.pl/solectwa-2'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]mieszkaniegepperta\.pl/dwurnik\.php'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]military-prints\.com/caton_woodville\.htm'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]militaryarchitecture\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]mini\.sl\.se/sv/travelplanner'),  # bot rejected on site (masti)
    re.compile('.*[\./@]minorplanetcenter\.net'),  # bot rejected on site (masti)
    re.compile('.*[\./@]minorplanetcenter\.org'),  # bot rejected on site (masti)
    re.compile('.*[\./@]mirassolandia\.sp\.gov\.br'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]mks-mos\.bedzin\.pl'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]mmanews\.pl'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]mogiel\.net/POL/history/polhist.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]monitorkonstytucyjny\.eu/archiwa'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]monitorpolski\.gov.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]movie-censorship\.com'),  # bot rejected on site (masti, ptjackyll)
    re.compile('.*[\./@]mpkolsztyn\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]mpu\.bydgoszcz\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]mrkoll\.se/person'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]msz\.gov\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]mtr\.com\.hk/en/customer/services/system_map.html'),  # bot rejected on site (masti)
    re.compile('.*[\./@]murki\.pl/ppm\.skaly\.Mirachowo\.acs'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]musixmatch\.com'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]muzeumgdansk\.pl/o-muzeum-gdanska/zarzad-i-rada-muzeum-gdanska'),  # bot rejected on site (masti)
    re.compile('.*[\./@]muzeumtg\.pl'),  # bot rejected on site (masti, Gabriel3)
    re.compile('.*[\./@]nasipolitici\.cz'),  # slow site (masti)
    re.compile('.*[\./@]nature\.com(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]nba\.com(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]neb\.de'),  # bot rejected on site (masti, Michozord)
    re.compile('.*[\./@]neonmuzeum\.org'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]nga\.gov/collection/gallery/gg60b/gg60b-main1\.html'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]nicesport\.pl/sportyzimowe/105016/mitz-mistrzem-szwecji'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]nicesport\.pl/sportyzimowe/109610/ps-w-planicy-214-metrow-muellera'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]nicesport\.pl/sportyzimowe/138514/pk-w-engelbergu-schmitt-wygrywa-serie-probna-nowy-rekord-grecji'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]nicesport\.pl/sportyzimowe/140101/fc-w-rasnovie-znamy-liste-uczestnikow'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]nicesport\.pl/sportyzimowe/142712/ps-w-oberstdorfie-seria-probna-dla-kranjca-kolejny-rekord-bulgarii'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]niezalezna\.pl'),  # false positive (masti)
    re.compile('.*[\./@]nike\.org\.pl/strona\.php\?p='),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]norden\.org'),  # slow site (masti)
    re.compile('.*[\./@]norfolkchurches\.co\.uk'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]nowadekada\.pl'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]noweskalmierzyce\.pl/pl/strona/parki-krajobrazowe'),  # bot rejected on site (masti)
    re.compile('.*[\./@]nra\.lv/politika/128301-12-saeima-apstiprinata\.htm'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]nssdc\.gsfc\.nasa\.gov/nmc/spacecraft/display\.action?id='),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]nssdc\.gsfc\.nasa\.gov/nmc/spacecraft/display\.action?id='),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]nssdc\.gsfc\.nasa\.gov/nmc/spacecraft/display\.action\?id='),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]nssdc\.gsfc\.nasa\.gov/planetary/factsheet/earthfact\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]nssdc\.gsfc\.nasa\.gov/planetary/factsheet/neptuniansatfact\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]nssdc\.gsfc\.nasa\.gov/planetary/factsheet/sunfact\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]nssdc\.gsfc\.nasa\.gov/planetary/gemini_4_eva\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]nztop40\.co\.nz/index.php/chart/singles'),  # bot rejected on site (masti)
    re.compile('.*[\./@]obc\.opole\.pl/dlibra/publication/edition/1076?id=1076'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]obc\.opole\.pl/dlibra/publication/edition/6609?id=6609'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]obc\.opole\.pl/dlibra/publication/edition/6661?id=6661'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]obywatelenauki\.pl/2014/02/wiecej-dobrej-nauki-nowa-akcja-prof-janusza-bujnickiego'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]ochtrup\.de'),  # bot rejected on site (masti)
    re.compile('.*[\./@]old\.iupac\.org/publications/books/rbook/Red_Book_2005\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]omulecki\.com'),  # bot rejected on site (masti, Cloefor)
    re.compile('.*[\./@]operakrolewska\.pl/artysci-2 '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]operone\.de/komponist/stefanijo\.html'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]opowiecie\.info/regionalna-mniejszosc-wiekszoscia-nowa-partia-lada-dzien/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]orzeczenia\.nsa\.gov\.pl/doc/'),  # bot rejected on site (masti)
    re.compile('.*[\./@]osnews\.pl(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]ossolineum\.pl/index\.php/aktualnosci/historia-znio/dyrektorzy-znio'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ossolineum\.pl/index\.php/aktualnosci/zbiory-lwowskie'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ostpommern\.de/kr-regenwalde.php'),  # bot rejected on site (masti)
    re.compile('.*[\./@]ostpommern\.de/kr-schlawe.php'),  # bot rejected on site (masti)
    re.compile('.*[\./@]ostrorog\.pl/asp/pl_start\.asp\?typ=14&menu=16&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ostrzeszow\.pl/asp/pl_start\.asp\?typ=14&menu=63&strona=1&prywatnosc=tak'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ostrzeszow\.pl/asp/pl_start\.asp\?typ=14&menu=89&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]other\.birge\.ru'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]otz\.de/web/zgt/politik/detail/-/specific/Fusionen-im-Altenburger-Land-Kreis-Greiz-und-Saalfeld-Rudolstadt-nun-moeglich-1908536788'),  # false positive (masti)
    re.compile('.*[\./@]oxfordmusiconline\.com\/subscriber/(/.*)?'),  # paywall  (masti)
    re.compile('.*[\./@]panstwo\.net'),  # bot rejected on site (masti)
    re.compile('.*[\./@]parafiapcim\.pl'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]parlament2015\.pkw\.gov\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]parlamentarny\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]parlamento\.pt(/.*)?'),  # slow response  (masti)
    re.compile('.*[\./@]partitodemocratico\.it/profile/stefano-bonaccini/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]pbn\.nauka\.gov\.pl/sedno-webapp/persons/969455/Tomasz_Maszczyk'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]pbn\.nauka\.gov\.pl/sedno-webapp/search'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]pcworld\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]pe2014\.pkw\.gov\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]perseus\.tufts\.edu/hopper/text?doc=Perseus%3Atext%3A1999\.04\.0057%3Aentry%3De%29ruqro%2Fs'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]pgeenergiaciepla\.pl/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]pingzhen\.tycg\.gov\.tw'),  # bot rejected on site (masti)
    re.compile('.*[\./@]piotrdlubak\.com'),  # bot rejected on site (masti, Cloefor)
    re.compile('.*[\./@]pl.linkedin\.com/pub/sabina-nowosielska/51/308/5a7'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]planespotters\.net'),  # bot rejected on site (masti)
    re.compile('.*[\./@]plantes-botanique\.org'),  # false positive (masti)
    re.compile('.*[\./@]plymouthherald\.co\.uk'),  # bot rejected on site (masti)
    re.compile('.*[\./@]pmaa\.pl/uczestnicy-2014 '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]pnf\.pl'),  # false positive (masti)
    re.compile('.*[\./@]pod-semaforkiem\.aplus\.pl/gt-chelmno\.php'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]poesies\.net/henrideregnier\.html'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]pointstreak\.com'),  # false positive (masti)
    re.compile('.*[\./@]polkiwravensbruck\.pl/zofii-pocilowska-kann/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]polski-dubbing\.pl/forum/viewtopic\.php?p=12114'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]polsteam\.com'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]polsteam\.com'),  # bot rejected on site (masti, Wiklol)
    re.compile('.*[\./@]portalpasazera\.pl/Plakaty'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]portalsamorzadowy\.pl'),  # false positive (masti)
    re.compile('.*[\./@]portugal\.gov\.pt/pt/gc21/comunicacao/noticia\?i=elenco-completo-do-novo-governo'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]postal-codes\.findthedata\.com'),  # false positive (masti)
    re.compile('.*[\./@]powiatwlodawski\.pl/c/document_library/get_file\?p_l_id=26096&folderId=34447&name=DLFE-1403\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]pracownia52\.pl/www/?p=7072 '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]prawo\.sejm\.gov\.pl/isap\.nsf/DocDetails\.xsp?id=WDU20120000124'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]president\.ee/en/estonia/decorations/bearers\.php\?id=1749'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]president\.gov\.ua(/.*)?'),  # redirect loop  (masti)
    re.compile('.*[\./@]pressto\.amu\.edu\.pl'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]proszynski\.pl/Historia-a-11-4-\.html'),  # bot rejected on site (masti, Zwistun2010)
    re.compile('.*[\./@]przegladlubartowski\.pl/informacje/6762/wybory-2014-wyniki-wyborow-wojtow-i-radnych'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]przewodnik-katolicki\.pl(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]przystanekplanszowka\.pl/2012/09/k2-wyrok.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]przystanekplanszowka\.pl/2012/10/dominion-rozdarte-krolewstwo-wyrok.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]przystanekplanszowka\.pl/2015/07/instrukcja-neuroshima-epub-mobi.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]pttk.gubin.com\.pl/luz/wycieczki.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]pwm\.com\.pl/pl/kompozytorzy_i_autorzy/5103/andrzej-nikodemowicz/index.html '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]pzbs\.pl/regulaminy-stale/137-regulamin-klasyfikacyjny'),  # bot rejected on site (masti)
    re.compile('.*[\./@]pzd-srem\.pl/asp'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]pzhl\.org\.pl/files/absolwencisms\.doc'),  # slow response (masti)
    re.compile('.*[\./@]raciborz\.com\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]raciborz\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]rada\.gov\.ua(/.*)?'),  # bot rejected on the site  (masti)
    re.compile('.*[\./@]radawarszawy\.um\.warszawa.pl'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]radioartnet\.net/11/2015/11/01/robert-adrian-smith-1935-2015-the-artist-and-the-media-condition'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]radomysl\.pl/asp'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]radzymin\.pl/asp/pliki/0000_Aktualnosci_2016/program_rewitalizacji_gminy_radzymin_24-04-2017\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]raimondspauls\.lv/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]rain-tree\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]rallye-info\.com'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rateyourmusic\.com'),  # false positive (masti)
    re.compile('.*[\./@]rcin\.org\.pl/dlibra/publication/15454'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rcin\.org\.pl/dlibra/publication/edition/2236?id=2236&from=publication'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rcin\.org\.pl/dlibra/publication/edition/2236?id=2236&from=publication'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rcin\.org\.pl/dlibra/publication/edition/2236\?id=2236&from=publication'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rcin\.org\.pl/dlibra/show-content/publication/edition/31639?id=31639'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rcin\.org\.pl/dlibra/show-content/publication/edition/31639\?id=31639'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rcin\.org\.pl/dlibra/show-content/publication/edition/5969?id=5969'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]redemptor\.pl'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]rehden\.de'),  # bot rejected on site (masti)
    re.compile('.*[\./@]rejestry-notarialne\.pl/37'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]rektor\.us\.edu\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]relacjebiograficzne\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]researchgate\.net'),  # bot rejected on site (masti)
    re.compile('.*[\./@]researchgate\.net/publication'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]ringostarr\.com'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rj\.metropoliaztm\.pl/przystanki/tarnowskie-gory'),  # bot rejected on site (masti, Gabriel3)
    re.compile('.*[\./@]rogowo\.paluki\.pl/asp/pliki/aktualnosci/ewidencja_pomnikow_przyrody\.pdf'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]rottentomatoes\.com(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]rozklad\.zdkium\.walbrzych\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]rsssf\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]rus\.delfi\.ee/daily/estonia/centristskaya-frakciya-v-parlamente-po-chislennosti-teper-lish-tretya\.d\?id=64222901'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]russiavolley\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]rymanow\.pl/asp'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/berdyczow0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/bychow0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/czerkasy0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/czortkow\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/dorpat0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/halicz0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/kamieniec-litewski0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/kamieniec0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/kijow0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/lojow0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/miadziol\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/mitawa0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/polock0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/ponary\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/pop-iwan0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/rewel0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/rowne0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/ryga0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/siebiez0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/trubczewsk0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/tuhanowicze0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/winnica0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/wornie0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/zabie0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzecz-pospolita\.com/zielence0\.php3'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]rzeszow-news\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]rzezawa\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]saeima\.lv/lv/aktualitates/saeimas-zinas/21757-saeima-apstiprina-deputata-pilnvaras-un-atjauno-mandatu-sesiem-deputatiem'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]samborzec\.pl/asp/_pdf\.asp\?typ=14&sub=2&subsub=72&menu=87&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]samborzec\.pl/asp/pl_start\.asp\?typ=14&sub=2&subsub=72&menu=80&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]samborzec\.pl/asp/pl_start\.asp\?typ=14&sub=31&subsub=121&menu=162&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]samborzec\.pl/asp/pliki/pobierz/LPR_Samborzec_281008\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]samorzad2014\.pkw\.gov\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/dlibra/docmetadata\?id=56'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/1000'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/1011'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/1015'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/1030'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/1031'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/1032'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/1033'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/1034'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/1047'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/1067'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/1070'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/350'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/351'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sanockabibliotekacyfrowa\.pl/publication/408'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]savatage\.com/newsavatage/discography/albums/edgeofthorns/info\.html'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]savatage\.com/newsavatage/discography/albums/edgeofthorns/info\.html'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]sbc\.org\.pl/dlibra'),  # bot rejected on site (masti)
    re.compile('.*[\./@]sbc\.org\.pl/publication/11793'),  # bot rejected on site (masti)
    re.compile('.*[\./@]scholar\.google\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]science\.ksc\.nasa\.gov(/.*)?'),  # very slow response resulting in bot error
    re.compile('.*[\./@]sdlp\.ie'),  # bot rejected on site (masti)
    re.compile('.*[\./@]senat\.ro'),  # slow site (masti)
    re.compile('.*[\./@]senate\.gov'),  # bot rejected on site (masti)
    re.compile('.*[\./@]seriea\.pl(/.*)?'),  # slow response  (masti)
    re.compile('.*[\./@]setkab\.go\.id/11-duta-besar-negara-sahabat-serahkan-surat-kepercayaan-kepada-presiden-jokowi'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]shantymen\.pl'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]shmetro\.com(/.*)?'),  # slow response  (masti)
    re.compile('.*[\./@]sittensen\.de'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sjdz\.jlu\.edu\.cn/CN/abstract/abstract8427\.shtml'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sjdz\.jlu\.edu\.cn/CN/abstract/abstract8427\.shtml'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sjp\.pwn\.pl/zasady/Transliteracja-i-transkrypcja-wspolczesnego-alfabetu-macedonskiego;629733\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]skisprungschanzen\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]sl\.se/ficktid/vinter/h22ny\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sledzinska-katarasinska\.pl/o-mnie'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]snooker\.org/res/index\.asp?event=281 -> http://www\.snooker\.org/res/index\.asp?event=281'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sns\.org\.rs'),  # bot rejected on site (masti)
    re.compile('.*[\./@]soccerbase\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]sosnowka\.pl/asp/pl_start\.asp\?typ=14&menu=11&strona=1&sub=10'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]sothebys\.com/es/auctions/ecatalogue/2014/medieval-renaissance-manuscripts-l14241/lot\.32\.html'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]speedwayresults\.com'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]spoilertv\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]spsarnow\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]sputniknews\.com/society/201803251062883119-israel-sculptor-death-meisler'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ssweb\.seap\.minhap\.es'),  # slow site (masti)
    re.compile('.*[\./@]stadtlohn\.de'),  # bot rejected on site (masti)
    re.compile('.*[\./@]stare-babice\.pl/sites/default/files/attachment/ludnosc_w_podziale_na_miejscowosci_2010_2015.pdf'),  # bot rejected on site (masti)
    re.compile('.*[\./@]stat\.gov\.pl/broker/access'),  # bot rejected on site (masti, Stok)
    re.compile('.*[\./@]stat\.gov\.pl/cps/rde/xbcr/gus/LU_ludnosc_stan_struktura_31_12_2012\.pdf'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]stat\.gov\.pl/download/gfx/portalinformacyjny/pl/defaultaktualnosci/5488/2/15/1/szkoly_wyzsze_i_ich_finanse_w_2018\.pdf'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]stat\.gov\.pl/download/gfx/portalinformacyjny/pl/defaultaktualnosci/5670/21/1/1/1_miejscowosci_ludnosc_nsp2011\.xlsx'),  # bot rejected on site (masti)
    re.compile('.*[\./@]stat\.gov\.pl/obszary-tematyczne/ludnosc/ludnosc/ludnosc-stan-i-struktura-ludnosci-oraz-ruch-naturalny-w-przekroju-terytorialnym-stan-w-dniu-31-12-2019,6,27\.html'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]stat\.gov\.pl/obszary-tematyczne/ludnosc/ludnosc/ludnosc-stan-i-struktura-w-przekroju-terytorialnym-stan-w-dniu-30-06-2019,6,26\.html'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]stat\.gov\.pl/obszary-tematyczne/ludnosc/ludnosc/powierzchnia-i-ludnosc-w-przekroju-terytorialnym-w-2019-roku,7,16\.html'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]statistics\.gr/documents/20181/1210503/resident_population_census2011rev\.xls/956f8949-513b-45b3-8c02-74f5e8ff0230'),  # file exists (masti)
    re.compile('.*[\./@]stratigraphy\.org(/.*)?'),  # site very slow timeouts  (masti)
    re.compile('.*[\./@]structurae\.net'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]suraz\.pl/asp/pl_start\.asp?typ=14&sub=7&menu=45&strona=1'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]svencionys\.lt/index.php?3819840680'),  # bot rejected on site (masti)
    re.compile('.*[\./@]swaid\.stat\.gov\.pl/Dashboards/Dane%20dla%20jednostki%20podzia%C5%82u%20terytorialnego\.aspx'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]swiatowedziedzictwo\.nid\.pl/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]switzenhausen\.eu'),  # bot rejected on site (masti)
    re.compile('.*[\./@]sztetl\.org\.pl/pl/miejscowosci/l/497-lodz/112-synagogi-domy-modlitwy-i-inne/86846-szczegolowy-spis-domow-modlitwy-w-lodzi'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]szukajwarchiwach\.pl'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]tablicerejestracyjne\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]teamusa\.org/USA-Wrestling/Features/2019/April/18/Coon-Nowry-Perkins-win-gold-at-Pan-Am-Championships-in-Buenos-Aires'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]teamusa\.org/USA-Wrestling/Team-USA/World-Team-History'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ted\.europa\.eu(/.*)?'),  # bot rejected on the site  (masti)
    re.compile('.*[\./@]tel-aviv\.millenium\.org\.il'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]tenisista\.com\.pl/ciekawostki-tenisowe\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]tenisista\.com\.pl/ewolucja-sprzetu-tenisowego\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]tenisista\.com\.pl/historia-tenisa\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]tenisista\.com\.pl/suzanne-lenglen\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]tenisista\.com\.pl/zasady-gry-w-tenisa\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]the-athenaeum\.org'),  # bot rejected on site (masti)
    re.compile('.*[\./@]the-athenaeum\.org/art/by_artist\.php?id=421'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]the-athenaeum\.org/art/list\.php?m=a&s=du&aid=1722'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]the-athenaeum\.org/art/list\.php?m=a&s=du&aid=551'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]the-athenaeum\.org/art/list\.php?m=a&s=du&aid=586'),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]the-sports\.org(/.*)?'),  # slow response  (masti)
    re.compile('.*[\./@]theplantlist\.org'),  # bot rejected on site (masti, Wiklol)
    re.compile('.*[\./@]tiger\.edu\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]tokarczuk\.wydawnictwoliterackie\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]torun\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]transport\.gov\.mg'),  # bot rejected on site (masti)
    re.compile('.*[\./@]trm\.md'),  # bot rejected on site (masti)
    re.compile('.*[\./@]trybunal\.gov\.pl/o-trybunale/sedziowie-trybunalu-konstytucyjnego/art/2440-slawomira-wronkowska-jaskiewicz/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]trzebiatow\.pl/asp/pl_start\.asp\?typ=14&sub=5&menu=49&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]trzebiatow\.pl/asp/pl_start\.asp\?typ=14&sub=9&menu=177&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]trzebiatow\.pl/asp/pl_start\.asp\?typ=14&sub=9&menu=63&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]tulospalvelu\.vaalit\.fi'),  # slow site (masti)
    re.compile('.*[\./@]tygodnikpowszechny\.pl(/.*)?'),  # bot redirect loop  (masti)
    re.compile('.*[\./@]udlaspalmas\.es/jugador/alvaro-lemos'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]udlaspalmas\.es/jugador/aythami-artiles-1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]udlaspalmas\.es/jugador/de-la-bella'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]udlaspalmas\.es/jugador/raul-fernandez'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]udlaspalmas\.es/jugador/ruiz-de-galarreta'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]udlaspalmas\.es/noticias/noticia/el-presidente-confirma-el-pago-a-boca-por-araujo]'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]udlaspalmas\.es/noticias/noticia/marko-livaja-cedido-al-aek-atenas'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ugcycow\.pl/asp/pl_start\.asp\?typ=13&sub=5&menu=6&artykul=2872&akcja=artykul'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ugcycow\.pl/asp/pl_start\.asp\?typ=14&sub=19&menu=35&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]ugsiedliszcze\.bip\.e-zeto\.eu/index\.php?type%3D4%26name%3Dbt46%26func%3Dselectsite%26value%255B0%255D%3Dmnu11%26value%255B1%255D%3D6'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]um\.warszawa\.pl/aktualnosci/kolekcja-ludwiga-zimmerera-juz-w-muzeum-etnograficznym'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]um\.zabrze\.pl/mieszkancy/miasto/historia/wladze-lokalne'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]um\.zabrze\.pl/mieszkancy/miasto/historia/wladze-lokalne'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]uniaeuropejska.org/antysemickie-hasa-w-wgierskim-parlamencie/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]uniaeuropejska.org/marek-safjan-ponownie-sedzia-tsue/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]uniwersytetradom\.pl/art/display_article\.php'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]upjp2\.edu\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]usnews\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]usopen\.org/en_US/visit/history/mschamps\.html'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]usopen\.org/index\.html'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]usosweb\.amu\.edu\.pl(/.*)?'),  # HTTP redirect loop on site  (masti)
    re.compile('.*[\./@]usps\.com'),  # bot rejected on site (masti)
    re.compile('.*[\./@]villaeva\.pl/villa-eva/historia'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]villargordodelcabriel\.es'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]vled\.co\.il'),  # bot rejected on site (masti)
    re.compile('.*[\./@]vreme\.com/cms/view\.php\?id=346508'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]waganiec\.biuletyn\.net/?bip=2&cid=37&id=36'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/pl/kurier-wawerski'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/pl/news/mapa-wawerskich-szlakow-rowerowych'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/pl/news/otwarcie-szlaku-rowerowego-mtb'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/sites/default/files/field/attachments/LAS%20PROGNOZA%20%C5%9ARODOWISKOWA%2004%202014\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/sites/default/files/field/attachments/Mapki%20szlak%C3%B3w\.jpg'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/sites/default/files/field/attachments/Opisy%20tras%20rowerowych\.doc]'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/sites/default/files/field/attachments/Wawer%20szlaki%201x1%2C4\.jpg'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/sites/default/files/kw_nr_05_2016_n_3\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/sites/default/files/nr_15_2012\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/sites/default/files/nr_20_2012\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/sites/default/files/nr_5_2012\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/sites/default/files/nr_6_2011\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wawer\.warszawa\.pl/sites/default/files/nr_7_2012\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wbc\.macbre\.net'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]wcsp\.science\.kew\.org'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wcsp\.science\.kew\.org/prepareChecklist\.do?checklist=selected_families%40%40222100820181252697'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]web\.archive\.org/web/20090805065419/http://www\.the-afc\.com/en/afc-u19-womens-championship-2009-schedule-a-results'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]website\.musikhochschule-muenchen\.de/de/index.php?option=com_content&task=view&id=636 '),  # bot rejected on site (masti, Fiszka)
    re.compile('.*[\./@]widawa\.pl/asp/pl_start\.asp?typ=13&menu=1&artykul=231&akcja=artykul'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]widawa\.pl/asp/pl_start\.asp?typ=13&menu=1&artykul=231&akcja=artykul'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]widawa\.pl/asp/pl_start\.asp\?typ=13&menu=1&artykul=231&akcja=artykul'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wielcy\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]wielkopolanie\.zhr\.pl/rozkazy/L4_2010\.pdf'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]wiki-de\.genealogy\.net/GOV:AUSERKJO72RN'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wiki-de\.genealogy\.net/GOV:KLEHOFJO82RV'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wiki-de\.genealogy\.net/GOV:KRIIELJO72QK'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wiki-de\.genealogy\.net/GOV:MEIITZKO03AH'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wiki-de\.genealogy\.net/GOV:VORSENJO72RM]'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wiki-de\.genealogy\.net/Gutt_%28Familienname%29'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wrecksite\.eu'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wupperverband\.de'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]bipraciborz\.pl/bip/dokumenty-akcja-wyszukaj-idkategorii-39906'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]ebelchatow\.pl/content/nie-plus-plus-polska-razem'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]europeanvoice\.com/folder/theswedishpresidencyoftheeu/124.aspx?artid=65305'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]federnuoto\.it/federazione/federazione-news/item/40079-barelli-eletto-alla-camera.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]forumakademickie\.pl/aktualnosci/2011/1/5/765/jak-ck-wybierano/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]forumakademickie\.pl/fa/2015/07-08/kronika-wydarzen/odzew-w-sprawie-bez-odzewu/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]gopsusports.com/sports/m-fenc/spec-rel/032402aaa.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]independent\.co\.uk/news/world/europe/mariano-rajoy-latest-spain-election-pedro-sanchez-premier-basque-national-party-a8378101.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]independent\.co\.uk/news/world/europe/mariano-rajoy-latest-spain-election-pedro-sanchez-premier-basque-national-party-a8378101.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]independent\.co\.uk/news/world/europe/silvio-berlusconis-heir-angelino-alfano-forms-new-party-in-italy-8943520.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]independent\.co\.uk/opinion/commentators/denis-macshane-britain-can-help-to-shape-a-new-europe-481214.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]leggiperme.it/?p=495'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]matica\.hr/knjige/autor/369/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]mojabibliotekamazurska\.pl/biblioteka/ukazaly_sie_02_03.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]msp\.gov\.pl/pl/media/aktualnosci/31579,Zmiany-w-kierownictwie-MSP.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]ordynacka\.pl/2017/04/22/zakonczyl-sie-vii-kongres-ordynackiej/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]pip\.gov\.pl/pl/wiadomosci/69784,roman-giedrojc-glownym-inspektorem-pracy.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]pism\.pl/publications/bulletin/no-55-905'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]ptp\.org\.pl/modules.php?name=News&file=article&sid=25'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]segodnya\.ua/politics/pnews/olga-bogomolec-sobiraetsya-ballotirovatsya-v-prezidenty-ukrainy-505598.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]wloclawek\.info.pl/nowosci,wiadomosci_wloclawek_i_region,1,1,tadeusz_dubicki_nowym_rektorem_p,16036.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]bielecki\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]businesseurope\.eu/history-organisation'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]faktyoswiecim\.pl/fakty/aktualnosci/15778-oswiecim-to-pewne-janusz-chwierut-wygral-w-pierwszej-turze'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]fiedler\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]fiedler\.pl/sub,pl,arkady-radoslaw-fiedler\.html'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]forumakademickie\.pl/fa/2014/04/kurczewscy'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]forumakademickie\.pl/fa/2015/06/jak-stracic-prestiz'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]frithjof-schmidt\.de'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]ft\.dk/Folketinget/findMedlem(/.*)?'), # bot rejected on site  (masti)
    re.compile('.*[\./@]gcatholic\.org/churches/'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/conference/'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/diocese/'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former//t1946\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/bagn0\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/iles0\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/micr0\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0036\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0037\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0038\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0039\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0040\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0041\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0042\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0045\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0047\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0049\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0050\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0059\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0060\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0061\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0150\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0156\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0164\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0166\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0167\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0170\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0171\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0174\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0181\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0187\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0212\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0216\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0219\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0221\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0229\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0239\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0241\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0248\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0255\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0256\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0267\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0270\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0273\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0279\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0283\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0284\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0287\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0291\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0296\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0305\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0308\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0311\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0312\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0315\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0316\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0317\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0318\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0320\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0323\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0324\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0328\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0338\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0340\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0341\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0344\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0351\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0352\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0355\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0356\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0406\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0476\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0666\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0670\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0672\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0682\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0688\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0805\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0806\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0869\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0872\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0874\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0875\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0876\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0878\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0879\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0880\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0881\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0885\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0887\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0888\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0892\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0896\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0899\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0901\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0902\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0906\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0907\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0909\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0943\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t0944\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1040\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1302\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1418\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1419\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1425\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1428\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1433\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1434\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1435\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1437\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1438\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1439\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1441\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1445\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1447\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1449\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1450\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1451\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1452\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1453\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1454\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1577\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1578\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1585\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1589\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1597\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1602\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1605\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1606\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1609\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1617\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1622\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1623\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1627\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1632\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1633\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1635\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1641\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1644\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1647\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1651\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1652\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1679\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1682\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1683\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1690\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1691\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1693\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1694\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1696\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1703\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1704\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1706\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1710\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1712\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1716\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1718\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1719\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1723\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1724\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1725\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1727\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1733\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1738\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1799\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1826\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1831\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1833\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1835\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1836\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1838\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1839\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1893\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1895\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1896\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1897\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1900\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1901\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1902\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1903\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1904\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1905\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1906\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1907\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1908\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1910\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1911\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1923\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1926\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1928\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1931\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1934\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1935\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1936\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1937\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1938\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1940\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1941\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1943\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1945\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1947\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1949\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1951\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1952\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1956\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1957\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1958\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1959\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1960\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1962\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1964\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1965\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1966\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1967\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1969\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1970\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1971\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1974\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1975\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1976\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1977\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1978\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1979\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1980\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1981\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1984\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t1987\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t2022\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t2063\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t2065\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t2075\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t3381\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t3383\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/former/t3398\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/nunciature/nunc017\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/nunciature/nunc076\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/nunciature/org202\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/nunciature/org204\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/nunciature/org207\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/nunciature/org210\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/dioceses/romancuria/'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/cardinals-title-c2\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/cardinals-title-c3\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-BAR\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-BR\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-BU\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-CR\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-DEC\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-DEM\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-DI\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-FI\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-GL\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-GR\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-H\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-K\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-KI\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-KR\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-L\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-LO\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-N\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-O\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-P\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-PE\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-PF\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-PL\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-PR\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-RO\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-SH\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-SK\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-SU\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-TI\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-VONH\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-VONS\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-W\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-WI\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-X\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/bishops-Z\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/card'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/officials-C\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/hierarchy/data/officials-S\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/orders/006\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/orders/009\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/orders/040\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]gcatholic\.org/orders/237\.htm'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]ibdb\.com(/.*)?'), #site automatically redirectong (masti)
    re.compile('.*[\./@]ireneuszras\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]jacektomczak\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]jadwigarotnicka\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]jerzymaslowski\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]jerzymaslowski\.pl/wp-content/uploads/2009/02/jmm5\.jpg'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]kedzierzynkozle\.pl/portal/index\.php?t=200&id=35673'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]kulanu-party\.co\.il/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]kulturalna\.warszawa\.pl/nagroda-literacka,1,10564\.html?locale=pl_PL'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]lincolnshire\.org/lincolnshire-sausage/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]maltauncovered\.com/valletta-capital-city/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]mfa\.gov\.pl/pl/aktualnosci/wiadomosci/nominacje_dla_nowych_ambasadorow_rp'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]mojamongolia\.com/moj-zyciorys'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]muzeumsg\.pl/images/Publikacje_1918_1939/70\.J\.Prochwicz\.pdf(/.*)?'),  # false postive  (masti)
    re.compile('.*[\./@]nba-allstar\.com/legends/rosters\.htm '),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]netcarshow\.com/ford/2017-fiesta/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]netcarshow\.com/opel/2018-crossland_x/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]netcarshow\.com/volkswagen/2018-tiguan_allspace/'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]newyorktheatreguide\.com/news/jl09/bacchae555183\.htm'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]odg\.mi\.it/node/30222'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]pcworld\.com/article/253200/googles_project_glass_teases_augmented_reality_glasses\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]prowincja\.com\.pl/autorzy/Jerzy-Wcisla,25'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]terzobinario\.it/elezioni-alessandro-battilocchio-eletto-alla-camera/131593'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]tubawyszkowa\.pl/aktualnosci/czytaj/4863/Kandydaci-KWW-Kukiz-15-pod-szczesliwa-siodemka'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]uj\.edu\.pl/documents/10172/24c02901-aecc-4d79-b067-6ab2fa71fb00'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]uniaeuropejska\.org/nominacje-do-nagrod-mep-awards'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]wrp\.pl/prof-dr-hab-eberhard-makosz-1932-2018'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]zbigniewkonwinski\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]www3.put.poznan\.pl/jubileusz/honoriscausa'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]wybory\.gov\.pl/pe2019'),  # temporary (masti, Elfhelm)
    re.compile('.*[\./@]wysokosc\.mapa\.info\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]yg-life\.com/archives'),  # bot rejected on site (masti)
    re.compile('.*[\./@]ygfamily\.com'),  # bot rejected on site (masti, Camomilla)
    re.compile('.*[\./@]yivo\.org/yiddishland-topo'),  # Err 201, bot rejected on site (masti, Maitake)
    re.compile('.*[\./@]youtube\.com/(/.*)?'),  # bot rejected on site  (masti)
    re.compile('.*[\./@]zagnansk\.pl/asp/pl_start\.asp\?typ=14&menu=174'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]zagraevsky\.com/democracy_engl.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]zagraevsky\.com/sloboda_book1.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]zagraevsky\.com/vsmz11.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]zagraevsky\.com/vsmz2.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]zagraevsky\.com/vsmz5.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]zagraevsky\.com/vsmz7.htm'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]zalesie\.pl/asp/pl_start\.asp\?typ=14&menu=31&strona=1'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]zaleszany\.pl/asp/pl_start\.asp\?typ=14&menu=239&strona=1&sub=6'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]zbigniewloskot\.pl'),  # bot rejected on site (masti, Ysska)
    re.compile('.*[\./@]zbp\.pl/wydarzenia/archiwum/wydarzenia/2016/marzec/medale-kopernika-dla-srodowiska-naukowego'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]zdw\.lublin\.pl'),  # bot rejected on site (masti)
    re.compile('.*[\./@]zeglarski.info/artykuly/zmarl-kapitan-zygrfyd-zyga-perlicki/'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]zgryglas\.pl/o-mnie'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]zso\.bystrzyca\.eu'),  # bot rejected on site (masti)
    re.compile('.*[\./@]zulawy\.infopl\.info/index\.php/pndg/gstegna/drewnica'),  # bot rejected on site (masti, szoltys)
    re.compile('.*[\./@]zwierzyniec\.e-biuletyn\.pl/index\.php?id=131'),  # bot rejected on site (masti, szoltys)
    re.compile('\.*[\./@]assaeroporti\.com/statistiche'),  # bot rejected on site (masti, szoltys)
    re.compile('\.*[\./@]en\.jerusalem-patriarchate\.info/apostolic-succession'),  # bot rejected on site (masti, szoltys)
    re.compile('\.*[\./@]geonames\.nga\.mil/gns/html'),  # bot rejected on site (masti, szoltys)
    re.compile('\.*[\./@]iwf.net/results/athletes/?athlete=artykov-izzat-1993-09-08&id=2770'),  # bot rejected on site (masti, BrakPomysłuNaNazwę)
    re.compile('\.*[\./@]lizakowski-photo\.art\.pl'),  # bot rejected on site (masti, Cloefor)
    re.compile('\.*[\./@]s2\.fbcdn\.pl/5/clubs/40695/data/docs/pomorzanka-statystyka-1955-2011\.pdf'),  # bot rejected on site (masti, szoltys)
    re.compile('\.*[\./@]stat\.gov\.pl/spisy-powszechne/nsp-2011/nsp-2011-wyniki/ludnosc-w-miejscowosciach-statystycznych-wedlug-ekonomicznych-grup-wieku-stan-w-dniu-31-03-2011-r-,21,1\.html'),  # bot rejected on site (masti, szoltys)
    re.compile('\.*[\./@]www\.biuletyn\.net/nt-bin/start\.asp\\?podmiot=zaklikow/&strona=14&typ=podmenu&typmenu=14&menu=7&id=31&str=1'),  # bot rejected on site (masti, szoltys)
# gcatholic.org
    re.compile('.*[\./@]kpbc\.umk\.pl'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]friedensfahrt-museum\.de'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]opera\.lv'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]museum\.gov\.rw'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]reh4mat\.com/cbr/historia-zaopatrzenia-ortotycznego'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]structurae\.net/de'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]thames\.me\.uk/s00820\.htm'),  # bot rejected on site (masti, Four.mg)
    re.compile('.*[\./@]forecki\.pl'),  # bot rejected on site (masti, Cloefor)
    re.compile('.*[\./@]olimpijski\.pl'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]globalsecurity\.org/military/systems'),  # bot rejected on site (masti, Szoltys)
    re.compile('.*[\./@]e-dziennik\.mswia\.gov\.pl/DUM_MSW'),  # bot rejected on site (masti, Elfhelm)
    re.compile('.*[\./@]sport24\.ee'),  # bot rejected on site (masti, Barcival)
]


def _get_closest_memento_url(url, when=None, timegate_uri=None):
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


def get_archive_url(url):
    """Get archive URL."""
    try:
        archive = _get_closest_memento_url(
            url,
            timegate_uri='http://web.archive.org/web/')
    except Exception:
        archive = _get_closest_memento_url(
            url,
            timegate_uri='http://timetravel.mementoweb.org/webcite/timegate/')

    # FIXME: Hack for T167463: Use https instead of http for archive.org links
    if archive.startswith('http://web.archive.org'):
        archive = archive.replace('http://', 'https://', 1)
    return archive

def citeArchivedLink(link, text):
        #look if link is in cite template with non empty archive param
        #or link itself is an archive
        # return True in this cases

        temppars = textlib.extract_templates_and_params(text,remove_disabled_parts=True, strip=True)

        for (t,p) in temppars:
            if t.lower().startswith("cytuj"):
                #pywikibot.output(u'T:%s\nP:%s' % (t,p))
                arch = False
                urlin = False
                if 'archiwum' in p.keys():
                    if p['archiwum'].startswith(link):
                        #skip archive links
                        pywikibot.output('[%s] citeArchivedLink is archive:%s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),link))
                        return(True)
                    arch = len(p['archiwum'])
                    #if arch:
                    #    pywikibot.output('[%s] citeArchivedLink archive found:%s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),link))
                if 'url' in p.keys():
                    urlin = p['url'].startswith(link)
                    #pywikibot.output('[%s] citeArchivedLink link found:%s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),link))
                if arch and urlin:
                    pywikibot.output('[%s] citeArchivedLink link archived:%s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),link))
                    return(True)
        return(False)

def weblinksIn(text, withoutBracketed=False, onlyBracketed=False):
    """
    Yield web links from text.

    TODO: move to textlib
    """
    text = textlib.removeDisabledParts(text)

    # Ignore links in fullurl template
    text = re.sub(r'{{\s?fullurl:.[^}]*}}', '', text)

    # MediaWiki parses templates before parsing external links. Thus, there
    # might be a | or a } directly after a URL which does not belong to
    # the URL itself.

    # First, remove the curly braces of inner templates:
    nestedTemplateR = re.compile(r'{{([^}]*?){{(.*?)}}(.*?)}}')
    while nestedTemplateR.search(text):
        text = nestedTemplateR.sub(r'{{\1 \2 \3}}', text)

    # Then blow up the templates with spaces so that the | and }} will not
    # be regarded as part of the link:.
    templateWithParamsR = re.compile(r'{{([^}]*?[^ ])\|([^ ][^}]*?)}}',
                                     re.DOTALL)
    while templateWithParamsR.search(text):
        text = templateWithParamsR.sub(r'{{ \1 | \2 }}', text)

    # Add <blank> at the end of a template
    # URL as last param of multiline template would not be correct
    text = text.replace('}}', ' }}')

    # Remove HTML comments in URLs as well as URLs in HTML comments.
    # Also remove text inside nowiki links etc.
    text = textlib.removeDisabledParts(text)
    linkR = textlib.compileLinkR(withoutBracketed, onlyBracketed)
    for m in linkR.finditer(text):
        if m.group('url'):
            #pywikibot.output('URL to YIELD:%s' % m.group('url'))
            if not citeArchivedLink(m.group('url'),text):
                yield m.group('url')
            else:
                #test output
                #pywikibot.output('[%s] WebLinksIn: link skipped:%s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),m.group('url')))
                pass
        #else:
        #    yield m.group('urlb')

XmlDumpPageGenerator = partial(
    _XMLDumpPageGenerator, text_predicate=weblinksIn)


class NotAnURLError(BaseException):

    """The link is not an URL."""


@deprecated('requests', since='20160120', future_warning=True)
class LinkChecker:

    """
    Check links.

    Given a HTTP URL, tries to load the page from the Internet and checks if it
    is still online.

    Returns a (boolean, string) tuple saying if the page is online and
    including a status reason.

    Per-domain user-agent faking is not supported in this deprecated class.

    Warning: Also returns false if your Internet connection isn't working
    correctly! (This will give a Socket Error)

    """

    def __init__(self, url, redirectChain=[], serverEncoding=None,
                 HTTPignore=[]):
        """
        Initializer.

        redirectChain is a list of redirects which were resolved by
        resolveRedirect(). This is needed to detect redirect loops.
        """
        self.url = url
        self.serverEncoding = serverEncoding

        fake_ua_config = config.fake_user_agent_default.get(
            'weblinkchecker', False)
        if fake_ua_config and isinstance(fake_ua_config, str):
            user_agent = fake_ua_config
        elif fake_ua_config:
            user_agent = comms.http.fake_user_agent()
        else:
            user_agent = comms.http.user_agent()
        self.header = {
            'user-agent': user_agent,
            'Accept': 'text/xml,application/xml,application/xhtml+xml,'
                      'text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
            'Accept-Language': 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Keep-Alive': '30',
            'Connection': 'keep-alive',
        }
        self.redirectChain = redirectChain + [url]
        self.changeUrl(url)
        self.HTTPignore = HTTPignore

    def getConnection(self):
        """Get a connection."""
        if self.scheme == 'http':
            return httpclient.HTTPConnection(self.host)
        elif self.scheme == 'https':
            return httpclient.HTTPSConnection(self.host)
        else:
            raise NotAnURLError(self.url)

    def getEncodingUsedByServer(self):
        """Get encodung used by server."""
        if not self.serverEncoding:
            with suppress(Exception):
                pywikibot.output(
                    'Contacting server %s to find out its default encoding...'
                    % self.host)
                conn = self.getConnection()
                conn.request('HEAD', '/', None, self.header)
                self.response = conn.getresponse()
                self.readEncodingFromResponse(self.response)

            if not self.serverEncoding:
                # TODO: We might also load a page, then check for an encoding
                # definition in a HTML meta tag.
                pywikibot.output("Error retrieving server's default charset. "
                                 'Using ISO 8859-1.')
                # most browsers use ISO 8859-1 (Latin-1) as the default.
                self.serverEncoding = 'iso8859-1'
        return self.serverEncoding

    def readEncodingFromResponse(self, response):
        """Read encoding from response."""
        if not self.serverEncoding:
            with suppress(Exception):
                ct = response.getheader('Content-Type')
                charsetR = re.compile('charset=(.+)')
                charset = charsetR.search(ct).group(1)
                self.serverEncoding = charset

    def changeUrl(self, url):
        """Change url."""
        self.url = url
        # we ignore the fragment
        (self.scheme, self.host, self.path, self.query,
         self.fragment) = urlsplit(self.url)
        if not self.path:
            self.path = '/'
        if self.query:
            self.query = '?' + self.query
        self.protocol = url.split(':', 1)[0]
        # check if there are non-ASCII characters inside path or query, and if
        # so, encode them in an encoding that hopefully is the right one.
        try:
            self.path.encode('ascii')
            self.query.encode('ascii')
        except UnicodeEncodeError:
            encoding = self.getEncodingUsedByServer()
            self.path = quote(self.path.encode(encoding))
            self.query = quote(self.query.encode(encoding), '=&')

    def resolveRedirect(self, useHEAD=False) -> Optional[str]:
        """
        Return the redirect target URL as a string, if it is a HTTP redirect.

        If useHEAD is true, uses the HTTP HEAD method, which saves bandwidth
        by not downloading the body. Otherwise, the HTTP GET method is used.
        """
        conn = self.getConnection()
        try:
            if useHEAD:
                conn.request('HEAD', '%s%s' % (self.path, self.query), None,
                             self.header)
            else:
                conn.request('GET', '%s%s' % (self.path, self.query), None,
                             self.header)
            self.response = conn.getresponse()
            # read the server's encoding, in case we need it later
            self.readEncodingFromResponse(self.response)
        except httpclient.BadStatusLine:
            # Some servers don't seem to handle HEAD requests properly,
            # e.g. http://www.radiorus.ru/ which is running on a very old
            # Apache server. Using GET instead works on these (but it uses
            # more bandwidth).
            if useHEAD:
                return self.resolveRedirect(useHEAD=False)
            else:
                raise
        if self.response.status >= 300 and self.response.status <= 399:
            # to debug, print response.getheaders()
            redirTarget = self.response.getheader('Location')
            if redirTarget:
                try:
                    redirTarget.encode('ascii')
                except UnicodeError:
                    redirTarget = redirTarget.decode(
                        self.getEncodingUsedByServer())
                if redirTarget.startswith(('http://', 'https://')):
                    self.changeUrl(redirTarget)
                    return True
                elif redirTarget.startswith('/'):
                    self.changeUrl('{0}://{1}{2}'
                                   .format(self.protocol, self.host,
                                           redirTarget))
                    return True
                else:  # redirect to relative position
                    # cut off filename
                    directory = self.path[:self.path.rindex('/') + 1]
                    # handle redirect to parent directory
                    while redirTarget.startswith('../'):
                        redirTarget = redirTarget[3:]
                        # some servers redirect to .. although we are already
                        # in the root directory; ignore this.
                        if directory != '/':
                            # change /foo/bar/ to /foo/
                            directory = directory[:-1]
                            directory = directory[:directory.rindex('/') + 1]
                    self.changeUrl('{0}://{1}{2}{3}'
                                   .format(self.protocol, self.host, directory,
                                           redirTarget))
                    return True
        else:
            return False  # not a redirect

    def check(self, useHEAD=False) -> Tuple[bool, str]:
        """Return True and the server status message if the page is alive."""
        try:
            wasRedirected = self.resolveRedirect(useHEAD=useHEAD)
        except UnicodeError as error:
            return False, 'Encoding Error: {0} ({1})'.format(
                error.__class__.__name__, error)
        except httpclient.error as error:
            return False, 'HTTP Error: {}'.format(error.__class__.__name__)
        except socket.error as error:
            # https://docs.python.org/3/library/socket.html :
            # socket.error :
            # The accompanying value is either a string telling what went
            # wrong or a pair (errno, string) representing an error
            # returned by a system call, similar to the value
            # accompanying os.error
            if isinstance(error, str):
                msg = error
            else:
                try:
                    msg = error[1]
                except IndexError:
                    pywikibot.output('### DEBUG information for T57282')
                    raise IndexError(type(error))
            # TODO: decode msg. On Linux, it's encoded in UTF-8.
            # How is it encoded in Windows? Or can we somehow just
            # get the English message?
            return False, 'Socket Error: {}'.format(repr(msg))
        if wasRedirected:
            if self.url in self.redirectChain:
                if useHEAD:
                    # Some servers don't seem to handle HEAD requests properly,
                    # which leads to a cyclic list of redirects.
                    # We simply start from the beginning, but this time,
                    # we don't use HEAD, but GET requests.
                    redirChecker = LinkChecker(
                        self.redirectChain[0],
                        serverEncoding=self.serverEncoding,
                        HTTPignore=self.HTTPignore)
                    return redirChecker.check(useHEAD=False)
                else:
                    urlList = ['[{0}]'.format(url)
                               for url in self.redirectChain + [self.url]]
                    return (False,
                            'HTTP Redirect Loop: {0}'.format(
                                ' -> '.join(urlList)))
            elif len(self.redirectChain) >= 19:
                if useHEAD:
                    # Some servers don't seem to handle HEAD requests properly,
                    # which leads to a long (or infinite) list of redirects.
                    # We simply start from the beginning, but this time,
                    # we don't use HEAD, but GET requests.
                    redirChecker = LinkChecker(
                        self.redirectChain[0],
                        serverEncoding=self.serverEncoding,
                        HTTPignore=self.HTTPignore)
                    return redirChecker.check(useHEAD=False)
                else:
                    urlList = ['[{0}]'.format(url)
                               for url in self.redirectChain + [self.url]]
                    return (False,
                            'Long Chain of Redirects: {0}'
                            .format(' -> '.join(urlList)))
            else:
                redirChecker = LinkChecker(self.url, self.redirectChain,
                                           self.serverEncoding,
                                           HTTPignore=self.HTTPignore)
                return redirChecker.check(useHEAD=useHEAD)
        else:
            try:
                conn = self.getConnection()
            except httpclient.error as error:
                return False, 'HTTP Error: {0}'.format(
                    error.__class__.__name__)
            try:
                conn.request('GET', '{0}{1}'.format(self.path, self.query),
                             None, self.header)
            except socket.error as error:
                return False, 'Socket Error: {0}'.format(repr(error[1]))
            try:
                self.response = conn.getresponse()
            except Exception as error:
                return False, 'Error: {0}'.format(error)
            # read the server's encoding, in case we need it later
            self.readEncodingFromResponse(self.response)
            # site down if the server status is between 400 and 499
            alive = not (400 <= self.response.status < 500)
            if self.response.status in self.HTTPignore:
                alive = False
            return alive, '{0} {1}'.format(self.response.status,
                                           self.response.reason)


class LinkCheckThread(threading.Thread):

    """A thread responsible for checking one URL.

    After checking the page, it will die.
    """

    def __init__(self, page, url, history, HTTPignore, day):
        """Initializer."""
        super().__init__()
        self.page = page
        self.url = url
        self.history = history
        self.header = {
            'Accept': 'text/xml,application/xml,application/xhtml+xml,'
                      'text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
            'Accept-Language': 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Keep-Alive': '30',
            'Connection': 'keep-alive',
        }
        # identification for debugging purposes
        self.setName(('{0} - {1}'.format(page.title(),
                                         url.encode('utf-8', 'replace'))))
        self.HTTPignore = HTTPignore
        self._use_fake_user_agent = config.fake_user_agent_default.get(
            'weblinkchecker', False)
        self.day = day

    def run(self):
        """Run the bot."""
        ok = False
        exception = False
        ignore = False
        try:
            header = self.header
            r = comms.http.fetch(
                self.url, headers=header,
                use_fake_user_agent=self._use_fake_user_agent)
        except requests.exceptions.InvalidURL:
            exception = True
            message = i18n.twtranslate(self.page.site,
                                       'weblinkchecker-badurl_msg',
                                       {'URL': self.url})
        except (pywikibot.exceptions.FatalServerError,requests.ConnectionError,Exception):
            exception = True
            message = 'Exception while connecting.'
            pywikibot.output('[{0}] Exception while processing URL {0} in page {1}'
                             .format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.url, self.page.title()))
            raise
        if not exception:
            if (r.status == requests.codes.ok
                    and str(r.status) not in self.HTTPignore):
                ok = True
            else:
                message = '{0}'.format(r.status)

        if ok:
            if self.history.setLinkAlive(self.url):
                pywikibot.output('*[{2}]:Link to {0} in [[{1}]] is back alive.'
                                 .format(self.url, self.page.title(),datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        else:
            pywikibot.output('*[{3}]:[[{0}]] links to {1} - {2}.'
                             .format(self.page.title(), self.url, message,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.history.setLinkDead(self.url, message, self.page,
                                     config.weblink_dead_days)


class History:

    """
    Store previously found dead links.

    The URLs are dictionary keys, and
    values are lists of tuples where each tuple represents one time the URL was
    found dead. Tuples have the form (title, date, error) where title is the
    wiki page where the URL was found, date is an instance of time, and error
    is a string with error code and message.

    We assume that the first element in the list represents the first time we
    found this dead link, and the last element represents the last time.

    Example::

     dict = {
         'https://www.example.org/page': [
             ('WikiPageTitle', DATE, '404: File not found'),
             ('WikiPageName2', DATE, '404: File not found'),
         ]
     }
    """

    def __init__(self, reportThread, site=None):
        """Initializer."""
        self.reportThread = reportThread
        if not site:
            self.site = pywikibot.Site()
        else:
            self.site = site
        self.semaphore = threading.Semaphore()
        self.datfilename = pywikibot.config.datafilepath(
            'deadlinks', 'deadlinks-{0}-{1}.dat'.format(self.site.family.name,
                                                        self.site.code))
        # Count the number of logged links, so that we can insert captions
        # from time to time
        self.logCount = 0
        try:
            with open(self.datfilename, 'rb') as datfile:
                self.historyDict = pickle.load(datfile)
            pywikibot.output('DICTIONARY LOADED: %i elements' % len(self.historyDict.keys()))
        except (IOError, EOFError):
            # no saved history exists yet, or history dump broken
            self.historyDict = {}
            pywikibot.output('SKIPPING INITIAL LOAD OF DATA')


    def log(self, url, error, containingPage, archiveURL):
        """Log an error report to a text file in the deadlinks subdirectory."""
        if archiveURL:
            errorReport = '* {0} ([{1} archiwum])\n'.format(url, archiveURL)
        else:
            errorReport = '* {0}\n'.format(url)
        for (pageTitle, date, error) in self.historyDict[url]:
            # ISO 8601 formulation
            isoDate = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(date))
            errorReport += '** In [[{0}]] on {1}, {2}\n'.format(
                pageTitle, isoDate, error)
        pywikibot.output('** Logging link for deletion.')
        txtfilename = pywikibot.config.datafilepath('deadlinks',
                                                    'results-{0}-{1}.txt'
                                                    .format(
                                                        self.site.family.name,
                                                        self.site.lang))
        with codecs.open(txtfilename, 'a', 'utf-8') as txtfile:
            self.logCount += 1
            if self.logCount % 30 == 0:
                # insert a caption
                txtfile.write('=== {} ===\n'
                              .format(containingPage.title()[:3]))
            txtfile.write(errorReport)

        if self.reportThread and not containingPage.isTalkPage():
            self.reportThread.report(url, errorReport, containingPage,
                                     archiveURL)

    def setLinkDead(self, url, error, page, weblink_dead_days):
        """Add the fact that the link was found dead to the .dat file."""
        with self.semaphore:
            now = time.time()
            if url in self.historyDict:
                timeSinceFirstFound = now - self.historyDict[url][0][1]
                timeSinceLastFound = now - self.historyDict[url][-1][1]
                # if the last time we found this dead link is less than an hour
                # ago, we won't save it in the history this time.
                if timeSinceLastFound > 60 * 60:
                    self.historyDict[url].append((page.title(), now, error))
                # if the first time we found this link longer than x day ago
                # (default is a week), it should probably be fixed or removed.
                # We'll list it in a file so that it can be removed manually.
                if timeSinceFirstFound > 60 * 60 * 24 * weblink_dead_days:
                    # search for archived page
                    try:
                        archiveURL = get_archive_url(url)
                    except Exception as e:
                        pywikibot.warning(
                            'get_closest_memento_url({0}) failed: {1}'.format(
                                url, e))
                        archiveURL = None
                    self.log(url, error, page, archiveURL)
            else:
                self.historyDict[url] = [(page.title(), now, error)]

    def setLinkAlive(self, url):
        """
        Record that the link is now alive.

        If link was previously found dead, remove it from the .dat file.

        @return: True if previously found dead, else returns False.
        """
        if url in self.historyDict:
            with self.semaphore, suppress(KeyError):
                del self.historyDict[url]
            return True

        return False

    def save(self):
        """Save the .dat file to disk."""
        #test output
        pywikibot.output('PICKLING %s records at %s' % (len(self.historyDict),datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        with open(self.datfilename, 'wb') as f:
            pickle.dump(self.historyDict, f, protocol=config.pickle_protocol)


class DeadLinkReportThread(threading.Thread):

    """
    A Thread that is responsible for posting error reports on talk pages.

    There is only one DeadLinkReportThread, and it is using a semaphore to make
    sure that two LinkCheckerThreads can not access the queue at the same time.
    """

    def __init__(self):
        """Initializer."""
        super().__init__()
        self.semaphore = threading.Semaphore()
        self.queue = []
        self.finishing = False
        self.killed = False

    def report(self, url, errorReport, containingPage, archiveURL):
        """Report error on talk page of the page containing the dead link."""
        with self.semaphore:
            self.queue.append((url, errorReport, containingPage, archiveURL))

    def shutdown(self):
        """Finish thread."""
        self.finishing = True

    def kill(self):
        """Kill thread."""
        # TODO: remove if unneeded
        self.killed = True

    def run(self):
        """Run thread."""
        while not self.killed:
            if len(self.queue) == 0:
                if self.finishing:
                    break
                else:
                    time.sleep(0.1)
                    continue

            with self.semaphore:
                url, errorReport, containingPage, archiveURL = self.queue[0]
                self.queue = self.queue[1:]
                talkPage = containingPage.toggleTalkPage()
                pywikibot.output(color_format(
                    '{lightaqua}** Reporting dead link on {}...{default}',
                    talkPage))
                try:
                    content = talkPage.get() + '\n'
                    if url in content:
                        pywikibot.output(color_format(
                            '{lightaqua}** Dead link seems to have '
                            'already been reported on {}{default}',
                            talkPage))
                        continue
                except (pywikibot.NoPage, pywikibot.IsRedirectPage):
                    content = ''

                if archiveURL:
                    archiveMsg = archiveURL
                else:
                    archiveMsg = ''


                # The caption will default to "Dead link". But if there
                # is already such a caption, we'll use "Dead link 2",
                # "Dead link 3", etc.
                #caption = i18n.twtranslate(containingPage.site,
                #                           'weblinkchecker-caption')
                caption = u'Martwy link'
                i = 1
                count = ''
                """
                # Check if there is already such a caption on
                # the talk page.
                while re.search('= *{0}{1} *='
                                .format(caption, count), content) is not None:
                    i += 1
                    count = ' ' + str(i)
                caption += count
                content += '== {0} ==\n\n{3}\n\n{1}{2}\n--~~~~'.format(
                    caption, errorReport, archiveMsg,
                    i18n.twtranslate(containingPage.site,
                                     'weblinkchecker-report'))

                comment = '[[{0}#{1}|→]] {2}'.format(
                    talkPage.title(), caption,
                    i18n.twtranslate(containingPage.site,
                                     'weblinkchecker-summary'))
                """
                # new code: use polish template
                content += u'{{Martwy link dyskusja\n | link=' + errorReport + u'\n | IA=' + archiveMsg + u'\n}}'

                comment = u'[[%s]] Robot zgłasza niedostępny link zewnętrzny: %s' % \
                          (talkPage.title(), url)

                try:
                    talkPage.put(content, comment)
                except pywikibot.SpamblacklistError as error:
                    pywikibot.output(color_format(
                        '{lightaqua}** SpamblacklistError while trying to '
                        'change {0}: {1}{default}',
                        talkPage, error.url))


class WeblinkCheckerRobot(SingleSiteBot, ExistingPageBot):

    """
    Bot which will search for dead weblinks.

    It uses several LinkCheckThreads at once to process pages from generator.
    """

    def __init__(self, generator, HTTPignore=None, day=7, site=True):
        """Initializer."""
        super().__init__(generator=generator, site=site)

        if config.report_dead_links_on_talk:
            pywikibot.log('Starting talk page thread')
            reportThread = DeadLinkReportThread()
            # thread dies when program terminates
            # reportThread.setDaemon(True)
            reportThread.start()
        else:
            reportThread = None
        self.history = History(reportThread, site=self.site)
        if HTTPignore is None:
            self.HTTPignore = []
        else:
            self.HTTPignore = HTTPignore
        self.day = day

        # Limit the number of threads started at the same time
        self.threads = ThreadList(limit=config.max_external_links,
                                  wait_time=config.retry_wait)

    def treat_page(self):
        """Process one page."""
        page = self.current_page
        """report  page.title and time"""
        try:
            pywikibot.output(u'P:%s >>>%s' % (page.title(), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        except:
            pass

        for url in weblinksIn(page.text):
            for ignoreR in ignorelist:
                if ignoreR.match(url):
                    break
            else:
                # Each thread will check one page, then die.
                thread = LinkCheckThread(page, url, self.history,
                                         self.HTTPignore, self.day)
                # thread dies when program terminates
                thread.setDaemon(True)
                self.threads.append(thread)


def RepeatPageGenerator():
    """Generator for pages in History."""
    history = History(None)
    pageTitles = set()
    for value in history.historyDict.values():
        for entry in value:
            pageTitles.add(entry[0])
    for pageTitle in sorted(pageTitles):
        page = pywikibot.Page(pywikibot.Site(), pageTitle)
        yield page


def countLinkCheckThreads() -> int:
    """
    Count LinkCheckThread threads.

    @return: number of LinkCheckThread threads
    """
    i = 0
    for thread in threading.enumerate():
        if isinstance(thread, LinkCheckThread):
            i += 1
    return i


@deprecated('requests', since='20160120', future_warning=True)
def check(url):
    """DEPRECATED: Use requests instead. Perform a check on URL."""
    return LinkChecker(url).check()


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    gen = None
    xmlFilename = None
    HTTPignore = []

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-talk':
            config.report_dead_links_on_talk = True
        elif arg == '-notalk':
            config.report_dead_links_on_talk = False
        elif arg == '-repeat':
            gen = RepeatPageGenerator()
        elif arg.startswith('-ignore:'):
            HTTPignore.append(int(arg[8:]))
        elif arg.startswith('-day:'):
            config.weblink_dead_days = int(arg[5:])
        elif arg.startswith('-xmlstart'):
            if len(arg) == 9:
                xmlStart = pywikibot.input(
                    'Please enter the dumped article to start with:')
            else:
                xmlStart = arg[10:]
        elif arg.startswith('-xml'):
            if len(arg) == 4:
                xmlFilename = i18n.input('pywikibot-enter-xml-filename')
            else:
                xmlFilename = arg[5:]
        else:
            genFactory.handleArg(arg)

    if xmlFilename:
        try:
            xmlStart
        except NameError:
            xmlStart = None
        gen = XmlDumpPageGenerator(xmlFilename, xmlStart,
                                   genFactory.namespaces)

    if not gen:
        gen = genFactory.getCombinedGenerator()
    if gen:
        if not genFactory.nopreload:
            # fetch at least 240 pages simultaneously from the wiki, but more
            # if a high thread number is set.
            pageNumber = max(20, config.max_external_links * 2)
            pywikibot.output("Fetch %i pages." % pageNumber)
            gen = pagegenerators.PreloadingGenerator(gen, groupsize=pageNumber)
        gen = pagegenerators.RedirectFilterPageGenerator(gen)
        bot = WeblinkCheckerRobot(gen, HTTPignore, config.weblink_dead_days)
        try:
            bot.run()
        except ImportError:
            suggest_help(missing_dependencies=('memento_client',))
            return False
        finally:
            waitTime = 0
            # Don't wait longer than 30 seconds for threads to finish.
            while countLinkCheckThreads() > 0 and waitTime < 30:
                try:
                    pywikibot.output('Waiting for remaining {0} threads to '
                                     'finish, please wait...'
                                     .format(countLinkCheckThreads()))
                    # wait 1 second
                    time.sleep(1)
                    waitTime += 1
                except KeyboardInterrupt:
                    pywikibot.output('Interrupted.')
                    break
            if countLinkCheckThreads() > 0:
                pywikibot.output('Remaining {0} threads will be killed.'
                                 .format(countLinkCheckThreads()))
                # Threads will die automatically because they are daemonic.
            if bot.history.reportThread:
                bot.history.reportThread.shutdown()
                # wait until the report thread is shut down; the user can
                # interrupt it by pressing CTRL-C.
                try:
                    while bot.history.reportThread.is_alive():
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    pywikibot.output('Report thread interrupted.')
                    bot.history.reportThread.kill()
            pywikibot.output('Saving history...')
            bot.history.save()
    else:
        suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
