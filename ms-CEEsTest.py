#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An incomplete sample script by masti for creating statistics/listings pages

This is not a complete bot; rather, it is a template from which simple
bots can be made. You can rename it to mybot.py, then edit it in
whatever way you want.

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

-v:               make verbose output
-vv:              make even more verbose output

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
import re

from pywikibot.bot import (
    MultipleSitesBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)
    #SingleSiteBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)
from pywikibot.tools import issue_deprecation_warning

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}
CEEtemplates = {'pl' : 'CEE Spring 2017','az' : 'Vikibahar 2017','ba' : 'Вики-яҙ 2017','be' : 'CEE Spring 2017','Be-tarask' : 'Артыкул ВікіВясны-2017','bg' : 'CEE Spring 2017','de' : 'CEE_Spring_2017','crh' : 'CEE Spring 2017','el' : 'CEE Spring 2017','myv' : 'ВикиТундо 2017','eo' : 'Viki-printempo 2017','hy' : 'CEE Spring 2017/հոդված','ka' : 'ვიკიგაზაფხული 2017','lv' : 'CEE Spring 2017','lt' : 'VRE 2017','mk' : 'СИЕ Пролет 2017','ro' : 'Wikimedia CEE Spring 2017','ru' : 'Вики-весна 2017','sq' : 'CEE Spring 2017','sr' : 'CEE Spring 2017','tt' : 'Вики-яз 2017','tr' : 'Vikibahar 2017','uk' : 'CEE Spring 2017','hu' : 'CEE Tavasz 2017' }
countryNames = {
'Albania' : { 'pl' : 'Albania', 'az' : 'Albaniya', 'ba' : 'Албания', 'be' : 'Албанія', 'Be-tarask' : 'Альбанія', 'bg' : 'Албания', 'de' : 'Albanien', 'crh' : 'Arnavutlıq', 'el' : 'Αλβανία', 'myv' : 'Албания', 'eo' : 'Albanio', 'hy' : 'Ալբանիա', 'ka' : 'ალბანეთი', 'lv' : 'Albānija', 'lt' : 'Albanija', 'mk' : 'Албанија', 'ro' : 'Albania', 'ru' : 'Албания', 'sq' : 'Shqipëria', 'sr' : 'Албанија', 'tt' : 'Албания', 'tr' : 'Arnavutluk', 'uk' : 'Албанія', 'hu' : 'Albánia'  },
'Austria' : { 'pl' : 'Austria', 'az' : 'Avstriya', 'ba' : 'Австрия', 'be' : 'Аўстрыя', 'Be-tarask' : 'Аўстрыя', 'bg' : 'Австрия', 'de' : 'Österreich', 'crh' : 'Avstriya', 'el' : 'Αυστρία', 'myv' : 'Австрия', 'eo' : 'Aŭstrio', 'hy' : 'Ավստրիա', 'ka' : 'ავსტრია', 'lv' : 'Austrija', 'lt' : 'Austrija', 'mk' : 'Австрија', 'ro' : 'Austria', 'ru' : 'Австрия', 'sq' : 'Austria', 'sr' : 'Аустрија', 'tt' : 'Австрия', 'tr' : 'Avusturya', 'uk' : 'Австрія', 'hu' : 'Ausztria'  },
'Azerbaijan' : { 'pl' : 'Azerbejdżan', 'az' : 'Azərbaycan', 'ba' : 'Әзербайжан', 'be' : 'Азербайджан', 'Be-tarask' : 'Азэрбайджан', 'bg' : 'Азербайджан', 'de' : 'Aserbaidschan', 'crh' : 'Azerbaycan', 'el' : 'Αζερμπαϊτζάν', 'myv' : 'Азербайджан', 'eo' : 'Azerbajĝano', 'hy' : 'Ադրբեջանական Հանրապետություն', 'ka' : 'აზერბაიჯანი', 'lv' : 'Azerbaidžāna', 'lt' : 'Azerbaidžanas', 'mk' : 'Азербејџан', 'ro' : 'Azerbaidjan', 'ru' : 'Азербайджан', 'sq' : 'Azerbajxhani', 'sr' : 'Азербејџан', 'tt' : 'Азәрбайҗан', 'tr' : 'Azerbaycan', 'uk' : 'Азербайджан', 'hu' : 'Azerbajdzsán'  },
'Bashkortostan' : { 'pl' : 'Baszkortostan', 'az' : 'Başqırdıstan', 'ba' : 'Башҡортостан', 'be' : 'Башкартастан', 'Be-tarask' : 'Башкартастан', 'bg' : 'Башкортостан', 'de' : 'Baschkortostan', 'crh' : 'Başqırtistan', 'el' : 'Μπασκορτοστάν', 'myv' : 'Башкирия', 'eo' : 'Baŝkirio', 'hy' : 'Բաշկորտոստան', 'ka' : 'ბაშკირეთი', 'lv' : 'Baškortostāna', 'lt' : 'Baškirija', 'mk' : 'Bashkortostani', 'ro' : 'Bașchiria', 'ru' : 'Башкортостан', 'sq' : 'Bashkortostani', 'sr' : 'Башкортостан', 'tt' : 'Башкортстан', 'tr' : 'Başkurdistan', 'uk' : 'Башкортостан', 'hu' : 'Baskirföld'  },
'Belarus' : { 'pl' : 'Białoruś', 'az' : 'Belarus', 'ba' : 'Беларусь', 'be' : 'Беларусь', 'Be-tarask' : 'Беларусь', 'bg' : 'Беларус', 'de' : 'Weißrussland', 'crh' : 'Belarus', 'el' : 'Λευκορωσία', 'myv' : 'Белорузия', 'eo' : 'Belorusio', 'hy' : 'Բելառուս', 'ka' : 'ბელარუსი', 'lv' : 'Baltkrievija', 'lt' : 'Baltarusija', 'mk' : 'Белорусија', 'ro' : 'Belarus', 'ru' : 'Белоруссия', 'sq' : 'Bjellorusia', 'sr' : 'Белорусија', 'tt' : 'Беларусия', 'tr' : 'Beyaz Rusya', 'uk' : 'Білорусь', 'hu' : 'Belorusz'  },
'Bulgaria' : { 'pl' : 'Bułgaria', 'az' : 'Bolqarıstan', 'ba' : 'Болгария', 'be' : 'Балгарыя', 'Be-tarask' : 'Баўгарыя', 'bg' : 'България', 'de' : 'Bulgarien', 'crh' : 'Bulğaristan', 'el' : 'Βουλγαρία', 'myv' : 'Болгария', 'eo' : 'Bulgario', 'hy' : 'Բուլղարիա', 'ka' : 'ბულგარეთი', 'lv' : 'Bulgārija', 'lt' : 'Bulgarija', 'mk' : 'Бугарија', 'ro' : 'Bulgaria', 'ru' : 'Болгария', 'sq' : 'Bullgaria', 'sr' : 'Бугарска', 'tt' : 'Болгария', 'tr' : 'Bulgaristan', 'uk' : 'Болгарія', 'hu' : 'Bulgária'  },
'Armenia' : { 'pl' : 'Armenia', 'az' : 'Ermənistan', 'ba' : 'Әрмәнстан', 'be' : 'Арменія', 'Be-tarask' : 'Армэнія', 'bg' : 'Армения', 'de' : 'Armenien', 'crh' : 'Ermenistan', 'el' : 'Αρμενία', 'myv' : 'Армения', 'eo' : 'Armenio', 'hy' : 'Հայաստան', 'ka' : 'სომხეთი', 'lv' : 'Armēnija', 'lt' : 'Armėnija', 'mk' : 'Ерменија', 'ro' : 'Armenia', 'ru' : 'Армения', 'sq' : 'Armenia', 'sr' : 'Јерменија', 'tt' : 'Әрмәнстан', 'tr' : 'Ermenistan', 'uk' : 'Вірменія', 'hu' : 'Örményország'  },
'Bosnia and Herzegovina' : { 'pl' : 'Bośnia i Hercegowina', 'az' : 'Bosniya və Herseqovina', 'ba' : 'Босния һәм Герцеговина', 'be' : 'Боснія і Герцагавіна', 'Be-tarask' : 'Босьнія і Герцагавіна', 'bg' : 'Босна и Херцеговина', 'de' : 'Bosnien und Herzegowina', 'crh' : 'Bosna ve Hersek', 'el' : 'Βοσνία και Ερζεγοβίνη', 'myv' : 'Босния ды Герцеговина', 'eo' : 'Bosnio kaj Hercegovino', 'hy' : 'Բոսնիա և Հերցեգովինա', 'ka' : 'ბოსნია და ჰერცეგოვინა', 'lv' : 'Bosnija un Hercegovina', 'lt' : 'Bosnija ir Hercegovina', 'mk' : 'Босна и Херцеговина', 'ro' : 'Bosnia și Herțegovina', 'ru' : 'Босния и Герцеговина', 'sq' : 'Bosnja dhe Hercegovina', 'sr' : 'Босна и Херцеговина', 'tt' : 'Босния һәм Герцеговина', 'tr' : 'Bosna-Hersek', 'uk' : 'Боснія і Герцеговина', 'hu' : 'Bosznia és Hercegovina'  },
'Erzia' : { 'pl' : 'Erzja', 'az' : 'Erzya', 'ba' : 'Эрзя', 'be' : 'Эрзя', 'Be-tarask' : 'Эрзя', 'bg' : 'Эрзя', 'de' : 'Ersja', 'el' : 'Έρζυα', 'myv' : 'Эрзя', 'eo' : 'Erzja',  'lv' : 'Erzju', 'lt' : 'Erzių', 'mk' : 'Ерзја', 'ru' : 'Эрзя', 'sr' : 'Ерзја', 'tt' : 'Ирзә', 'tr' : 'Erzya', 'uk' : 'Ерзя'  },
'Esperanto' : { 'pl' : 'Esperanto', 'az' : 'Esperantida', 'ba' : 'Эсперантида', 'be' : 'Эсперанта', 'Be-tarask' : 'Эспэранта', 'bg' : 'Есперанто', 'de' : 'Esperanto', 'crh' : 'Esperanto', 'el' : 'Εσπεράντο', 'myv' : 'Эсперанто', 'eo' : 'Esperanto', 'hy' : 'Էսպերանտո', 'ka' : 'ესპერანტო', 'lv' : 'Esperanto', 'lt' : 'Esperanto', 'mk' : 'Есперанто', 'ro' : 'Esperanto', 'ru' : 'Эсперанто', 'sq' : 'Gjuha esperanto', 'sr' : 'Есперанто', 'tt' : 'Эсперанто', 'tr' : 'Esperanto', 'uk' : 'Есперанто', 'hu' : 'Eszperantó'  },
'Estonia' : { 'pl' : 'Estonia', 'az' : 'Estoniya', 'ba' : 'Эстония', 'be' : 'Эстонія', 'Be-tarask' : 'Эстонія', 'bg' : 'Естония', 'de' : 'Estland', 'crh' : 'Estoniya', 'el' : 'Εσθονία', 'myv' : 'Эстэнь', 'eo' : 'Estonio', 'hy' : 'Էստոնիա', 'ka' : 'ესტონეთი', 'lv' : 'Igaunija', 'lt' : 'Estija', 'mk' : 'Естонија', 'ro' : 'Estonia', 'ru' : 'Эстония', 'sq' : 'Estonia', 'sr' : 'Естонија', 'tt' : 'Эстония', 'tr' : 'Estonya', 'uk' : 'Естонія', 'hu' : 'Észtország'  },
'Georgia' : { 'pl' : 'Gruzja', 'az' : 'Gürcüstan', 'ba' : 'Грузия', 'be' : 'Грузія', 'Be-tarask' : 'Грузія', 'bg' : 'Грузия', 'de' : 'Georgien', 'crh' : 'Gürcistan', 'el' : 'Γεωργία', 'myv' : 'Грузия', 'eo' : 'Kartvelio', 'hy' : 'Վրաստան', 'ka' : 'საქართველო', 'lv' : 'Gruzija', 'lt' : 'Gruzija', 'mk' : 'Грузија', 'ro' : 'Georgia', 'ru' : 'Грузия', 'sq' : 'Gjeorgjia', 'sr' : 'Грузија', 'tt' : 'Гөрҗистан', 'tr' : 'Gürcistan', 'uk' : 'Грузія', 'hu' : 'Grúzia'  },
'Czechia' : { 'pl' : 'Czechy', 'az' : 'Çexiya', 'ba' : 'Чехия', 'be' : 'Чэхія', 'Be-tarask' : 'Чэхія', 'bg' : 'Чехия', 'de' : 'Tschechien', 'crh' : 'Çehiya', 'el' : 'Τσεχία', 'myv' : 'Чехия', 'eo' : 'Ĉeĥio', 'hy' : 'Չեխիա', 'ka' : 'ჩეხეთი', 'lv' : 'Čehija', 'lt' : 'Čekija', 'mk' : 'Чешка', 'ro' : 'Cehia', 'ru' : 'Чехия', 'sq' : 'Republika Çeke', 'sr' : 'Чешка', 'tt' : 'Чехия', 'tr' : 'Çek Cumhuriyeti', 'uk' : 'Чехія', 'hu' : 'Csehország'  },
'Croatia' : { 'pl' : 'Chorwacja', 'az' : 'Xorvatiya', 'ba' : 'Хорватия', 'be' : 'Харватыя', 'Be-tarask' : 'Харватыя', 'bg' : 'Хърватия', 'de' : 'Kroatien', 'crh' : 'Hırvatistan', 'el' : 'Κροατία', 'myv' : 'Хорватия', 'eo' : 'Kroatio', 'hy' : 'Խորվաթիա', 'ka' : 'ხორვატია', 'lv' : 'Horvātija', 'lt' : 'Kroatija', 'mk' : 'Хрватска', 'ro' : 'Croația', 'ru' : 'Хорватия', 'sq' : 'Kroacia', 'sr' : 'Хрватска', 'tt' : 'Хорватия', 'tr' : 'Hırvatistan', 'uk' : 'Хорватія', 'hu' : 'Horvátország'  },
'Kosovo' : { 'pl' : 'Kosowo', 'az' : 'Kosovo', 'ba' : 'Косово', 'be' : 'Рэспубліка Косава', 'Be-tarask' : 'Косава', 'bg' : 'Косово', 'de' : 'Kosovo', 'crh' : 'Kosovo', 'el' : 'Κόσοβο', 'eo' : 'Kosovo', 'hy' : 'Կոսովո', 'ka' : 'კოსოვო', 'lv' : 'Kosova', 'lt' : 'Kosovas', 'mk' : 'Република Косово', 'ro' : 'Kosovo', 'ru' : 'Косово', 'sq' : 'Kosova', 'sr' : 'Република Косово', 'tt' : 'Косово Җөмһүрияте', 'tr' : 'Kosova', 'uk' : 'Косово', 'hu' : 'Koszovo'  },
'Crimean Tatars' : { 'pl' : 'Tatarzy krymscy', 'az' : 'Krım-Tatar', 'ba' : 'Ҡырым татарҙары', 'be' : 'Крымскія татары', 'Be-tarask' : 'Крымскія татары', 'bg' : 'Кримски татари', 'de' : 'Krimtataren', 'crh' : 'Qırımtatarlar', 'el' : 'Τατάροι Κριμαίας', 'eo' : 'Krime-tataroj', 'hy' : 'Ղրիմի թաթարներ', 'ka' : 'ყირიმელი თათრები', 'lv' : 'Krimas tatāri', 'lt' : 'Krymo totoriai', 'mk' : 'Кримски Татари', 'ro' : 'Tătarii crimeeni', 'ru' : 'Крымские татары', 'sr' : 'Кримски Татари', 'tt' : 'Кырым татарлары', 'tr' : 'Kırım Tatarları', 'uk' : 'Кримські татари', 'hu' : 'Krími tatárok'  },
'Lithuania' : { 'pl' : 'Litwa', 'az' : 'Litva', 'ba' : 'Литва', 'be' : 'Літва', 'Be-tarask' : 'Летува', 'bg' : 'Литва', 'de' : 'Litauen', 'crh' : 'Litvaniya', 'el' : 'Λιθουανία', 'myv' : 'Литва', 'eo' : 'Litovio', 'hy' : 'Լիտվա', 'ka' : 'ლიტვა', 'lv' : 'Lietuva', 'lt' : 'Lietuva', 'mk' : 'Литванија', 'ro' : 'Lituania', 'ru' : 'Литва', 'sq' : 'Lituania', 'sr' : 'Литванија', 'tt' : 'Литва', 'tr' : 'Litvanya', 'uk' : 'Литва', 'hu' : 'Litvánia'  },
'Latvia' : { 'pl' : 'Łotwa', 'az' : 'Latviya', 'ba' : 'Латвия', 'be' : 'Латвія', 'Be-tarask' : 'Латвія', 'bg' : 'Латвия', 'de' : 'Lettland', 'crh' : 'Latviya', 'el' : 'Λετονία', 'myv' : 'Латвия', 'eo' : 'Latvio', 'hy' : 'Լատվիա', 'ka' : 'ლატვია', 'lv' : 'Latvija', 'lt' : 'Latvija', 'mk' : 'Латвија', 'ro' : 'Letonia', 'ru' : 'Латвия', 'sq' : 'Letonia', 'sr' : 'Летонија', 'tt' : 'Latviä', 'tr' : 'Letonya', 'uk' : 'Латвія', 'hu' : 'Lettország'  },
'Hungary' : { 'pl' : 'Węgry', 'az' : 'Macarıstan', 'ba' : 'Венгрия', 'be' : 'Венгрыя', 'Be-tarask' : 'Вугоршчына', 'bg' : 'Унгария', 'de' : 'Ungarn', 'crh' : 'Macaristan', 'el' : 'Ουγγαρία', 'myv' : 'Мадьяронь', 'eo' : 'Hungario', 'hy' : 'Հունգարիա', 'ka' : 'უნგრეთი', 'lv' : 'Ungārija', 'lt' : 'Vengrija', 'mk' : 'Унгарија', 'ro' : 'Ungaria', 'ru' : 'Венгрия', 'sq' : 'Hungaria', 'sr' : 'Мађарска', 'tt' : 'Маҗарстан', 'tr' : 'Macaristan', 'uk' : 'Угорщина', 'hu' : 'Magyarország'  },
'Macedonia' : { 'pl' : 'Macedonia', 'az' : 'Makedoniya', 'ba' : 'Македония', 'be' : 'Македонія', 'Be-tarask' : 'Македонія', 'bg' : 'Македония', 'de' : 'Mazedonien', 'crh' : 'Makedoniya', 'el' : 'πΓΔΜ', 'myv' : 'Македония', 'eo' : 'Makedonio', 'hy' : 'Մակեդոնիայի Հանրապետություն', 'ka' : 'მაკედონია', 'lv' : 'Maķedonija', 'lt' : 'Makedonija', 'mk' : 'Македонија', 'ro' : 'Macedonia', 'ru' : 'Македония', 'sq' : 'Maqedonisë', 'sr' : 'Република Македонија', 'tt' : 'Македония', 'tr' : 'Makedonya', 'uk' : 'Македонія', 'hu' : 'Macedónia'  },
'Moldova' : { 'pl' : 'Mołdawia', 'az' : 'Moldova', 'ba' : 'Молдавия', 'be' : 'Малдова', 'Be-tarask' : 'Малдова', 'bg' : 'Молдова', 'de' : 'Moldawien', 'crh' : 'Moldova', 'el' : 'Μολδαβία', 'myv' : 'Молдавия', 'eo' : 'Moldava', 'hy' : 'Մոլդովա', 'ka' : 'მოლდოვა', 'lv' : 'Moldova', 'lt' : 'Moldavija', 'mk' : 'Молдавија', 'ro' : 'Moldova', 'ru' : 'Молдавия', 'sq' : 'Moldavia', 'sr' : 'Молдавија', 'tt' : 'Молдова', 'tr' : 'Moldova', 'uk' : 'Молдова', 'hu' : 'Moldávia'  },
'Poland' : { 'pl' : 'Polska', 'az' : 'Polşa', 'ba' : 'Польша', 'be' : 'Польшча', 'Be-tarask' : 'Польшча', 'bg' : 'Полша', 'de' : 'Polen', 'crh' : 'Lehistan', 'el' : 'Πολωνία', 'myv' : 'Польша', 'eo' : 'Pollando', 'hy' : 'Լեհաստան', 'ka' : 'პოლონეთი', 'lv' : 'Polija', 'lt' : 'Lenkija', 'mk' : 'Полска', 'ro' : 'Polonia', 'ru' : 'Польша', 'sq' : 'Polonia', 'sr' : 'Пољска', 'tt' : 'Польша', 'tr' : 'Polonya', 'uk' : 'Польща', 'hu' : 'Lengyelország'  },
'Russia' : { 'pl' : 'Rosja', 'az' : 'Rusiya', 'ba' : 'Рәсәй', 'be' : 'Расія', 'Be-tarask' : 'Расея', 'bg' : 'Русия', 'de' : 'Russland', 'crh' : 'Rusiye', 'el' : 'Ρωσία', 'myv' : 'Россия', 'eo' : 'Rusio', 'hy' : 'Ռուսաստան', 'ka' : 'რუსეთი', 'lv' : 'Krievija', 'lt' : 'Rusija', 'mk' : 'Русија', 'ro' : 'Rusia', 'ru' : 'Россия', 'sq' : 'Rusia', 'sr' : 'Русија', 'tt' : 'Русия', 'tr' : 'Rusya', 'uk' : 'Росія', 'hu' : 'Oroszország'  },
'Romania' : { 'pl' : 'Rumunia', 'az' : 'Rumıniya', 'ba' : 'Румыния', 'be' : 'Румынія', 'Be-tarask' : 'Румынія', 'bg' : 'Румъния', 'de' : 'Rumänien', 'crh' : 'Romaniya', 'el' : 'Ρουμανία', 'myv' : 'Румыния', 'eo' : 'Rumanio', 'hy' : 'Ռումինիա', 'ka' : 'რუმინეთი', 'lv' : 'Rumānija', 'lt' : 'Rumunija', 'mk' : 'Романија', 'ro' : 'România', 'ru' : 'Румыния', 'sq' : 'Rumania', 'sr' : 'Румунија', 'tt' : 'Румыния', 'tr' : 'Romanya', 'uk' : 'Румунія', 'hu' : 'Románia'  },
'Serbia' : { 'pl' : 'Republika Serbska', 'az' : 'Serb Respublikası', 'ba' : 'Серб Республикаһы', 'be' : 'Рэспубліка Сербская', 'Be-tarask' : 'Рэспубліка Сэрбская', 'bg' : 'Република Сръбска', 'de' : 'Republika Srpska', 'crh' : 'Sırb Cumhuriyeti', 'el' : 'Σερβική Δημοκρατία', 'myv' : 'Сербань Республикась', 'eo' : 'Serba Respubliko', 'hy' : 'Սերբական Հանրապետություն', 'ka' : 'სერბთა რესპუბლიკა', 'lv' : 'Serbu Republika', 'lt' : 'Serbų respublika', 'mk' : 'Република Српска', 'ro' : 'Republika Srpska', 'ru' : 'Республика Сербская', 'sr' : 'Република Српска', 'tr' : 'Sırp Cumhuriyeti', 'uk' : 'Республіка Сербська', 'hu' : 'Boszniai Szerb Köztársaság'  },
'Serbia' : { 'pl' : 'Serbia', 'az' : 'Serbiya', 'ba' : 'Сербия', 'be' : 'Сербія', 'Be-tarask' : 'Сэрбія', 'bg' : 'Сърбия', 'de' : 'Serbien', 'crh' : 'Sırbistan', 'el' : 'Σερβία', 'myv' : 'Сербия', 'eo' : 'Serbio', 'hy' : 'Սերբիա', 'ka' : 'სერბეთი', 'lv' : 'Serbija', 'lt' : 'Serbija', 'mk' : 'Србија', 'ro' : 'Serbia', 'ru' : 'Сербия', 'sq' : 'Serbia', 'sr' : 'Србија', 'tt' : 'Сербия', 'tr' : 'Sırbistan', 'uk' : 'Сербія', 'hu' : 'Szerbia'  },
'Slovakia ' : { 'pl' : 'Słowacja', 'az' : 'Slovakiya', 'ba' : 'Словакия', 'be' : 'Славакія', 'Be-tarask' : 'Славаччына', 'bg' : 'Словакия', 'de' : 'Slowakei', 'crh' : 'Slovakiya', 'el' : 'Σλοβακία', 'myv' : 'Словакия', 'eo' : 'Slovakio', 'hy' : 'Սլովակիա', 'ka' : 'სლოვაკეთი', 'lv' : 'Slovākija', 'lt' : 'Slovakija', 'mk' : 'Словачка', 'ro' : 'Slovacia', 'ru' : 'Словакия', 'sq' : 'Sllovakia', 'sr' : 'Словачка', 'tt' : 'Словакия', 'tr' : 'Slovakya', 'uk' : 'Словаччина', 'hu' : 'Szlovákia'  },
'Turkey' : { 'pl' : 'Turcja', 'az' : 'Türkiyə', 'ba' : 'Төркиә', 'be' : 'Турцыя', 'Be-tarask' : 'Турэччына', 'bg' : 'Турция', 'de' : 'Türkei', 'crh' : 'Türkiye', 'el' : 'Τουρκία', 'myv' : 'Турция', 'eo' : 'Turkio', 'hy' : 'Թուրքիա', 'ka' : 'თურქეთი', 'lv' : 'Turcija', 'lt' : 'Turkija', 'mk' : 'Турција', 'ro' : 'Turcia', 'ru' : 'Турция', 'sq' : 'Turqia', 'sr' : 'Турска', 'tt' : 'Төркия', 'tr' : 'Türkiye', 'uk' : 'Туреччина', 'hu' : 'Törökország'  },
'Ukraine' : { 'pl' : 'Ukraina', 'az' : 'Ukrayna', 'ba' : 'Украина', 'be' : 'Украіна', 'Be-tarask' : 'Украіна', 'bg' : 'Украйна', 'de' : 'Ukraine', 'crh' : 'Ukraina', 'el' : 'Ουκρανία', 'myv' : 'Украина', 'eo' : 'Ukrainio', 'hy' : 'Ուկրաինա', 'ka' : 'უკრაინა', 'lv' : 'Ukraina', 'lt' : 'Ukraina', 'mk' : 'Украина', 'ro' : 'Ucraina', 'ru' : 'Украина', 'sq' : 'Ukraina', 'sr' : 'Украјина', 'tt' : 'Украина', 'tr' : 'Ukrayna', 'uk' : 'Україна', 'hu' : 'Ukrajna'  },
'Greece' : { 'pl' : 'Grecja', 'az' : 'Yunanıstan', 'ba' : 'Греция', 'be' : 'Грэцыя', 'Be-tarask' : 'Грэцыя', 'bg' : 'Гърция', 'de' : 'Griechenland', 'crh' : 'Yunanistan', 'el' : 'Ελλάδα', 'myv' : 'Греция', 'eo' : 'Grekio', 'hy' : 'Հունաստան', 'ka' : 'საბერძნეთი', 'lv' : 'Grieķija', 'lt' : 'Graikija', 'mk' : 'Грција', 'ro' : 'Grecia', 'ru' : 'Греция', 'sq' : 'Greqia', 'sr' : 'Грчка', 'tt' : 'Греция', 'tr' : 'Yunanistan', 'uk' : 'Греція', 'hu' : 'Görögország'  },
'Kazakhstan' : { 'pl' : 'Kazachstan', 'az' : 'Qazaxıstan', 'ba' : 'Ҡаҙағстан', 'be' : 'Казахстан', 'Be-tarask' : 'Казахстан', 'bg' : 'Казахстан', 'de' : 'Kasachstan', 'crh' : 'Qazahistan', 'el' : 'Καζακστάν', 'myv' : 'Казахстан', 'eo' : 'Kazaĥio', 'hy' : 'Ղազախստան', 'ka' : 'ყაზახეთი', 'lv' : 'Kazahstāna', 'lt' : 'Kazachstanas', 'mk' : 'Казахстан', 'ro' : 'Kazahstan', 'ru' : 'Казахстан', 'sq' : 'Kazakistani', 'sr' : 'Казахстан', 'tt' : 'Казакъстан', 'tr' : 'Kazakistan', 'uk' : 'Казахстан', 'hu' : 'Kazahsztán'  }
}

class BasicBot(
    # Refer pywikobot.bot for generic bot classes
    #SingleSiteBot,  # A bot only working on one site
    MultipleSitesBot,  # A bot only working on one site
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
    springList = {}
    templatesList = {}
    authors = {}
    missingCount = {}
    pagesCount = {}
    women = {'pl':0, 'az':0, 'ba':0, 'be':0, 'be-tarask':0, 'bg':0, 'de':0, 'crh':0, 'el':0, 'myv':0, 'eo':0, 'hy':0, 'ka':0, 'lv':0, 'lt':0, \
             'mk':0, 'ro':0, 'ru':0, 'sq':0, 'sr':0, 'tt':0, 'tr':0, 'uk':0}
    countryp = { 'pl':'kraj', 'az':'ölkə', 'ba':'ил', 'be':'краіна', 'Be-tarask':'краіна', 'bg':'държава', 'de':'land', 'crh':'memleket', 'el':'country', \
                 'myv':'мастор', 'eo':'country', 'ka':'ქვეყანა', 'lv':'valsts', 'lt':'šalis', 'mk':'земја', 'ro':'țară', 'ru':'страна', 'sq':'country', \
                 'sr':'држава', 'tt':'ил', 'tr':'ülke', 'uk':'країна' }
    topicp = {'pl':'parametr', 'az':'qadınlar', 'ba':'тема', 'be':'тэма', 'Be-tarask':'тэма', 'bg':'тема', 'de':'thema', 'crh':'mevzu', 'el':'topic', \
             'myv':'тема', 'eo':'topic', 'ka':'თემა', 'lv':'tēma', 'lt':'tema', 'mk':'тема', 'ro':'subiect', 'ru':'тема', 'sq':'topic', 'sr':'тема', \
             'tt':'тема', 'tr':'konu', 'uk':'тема'}
    womenp = {'pl':'kobiety', 'az':'qadınlar', 'ba':'Ҡатын-ҡыҙҙар', 'be':'Жанчыны', 'Be-tarask':'жанчыны', 'bg':'жени', 'de':'Frauen', 'el':'γυναίκες', \
              'ka':'ქალები', 'lv':'Sievietes', 'mk':'Жени', 'ro':'Femei', 'ru':'женщины', 'sq':'Gratë', 'sr':'Жене', 'tt':'Хатын-кызлар', 'tr':'Kadın', 'uk':'жінки'}
    

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
            'testprint': False, # print testoutput
            'negative': False, #if True negate behavior i.e. mark pages that DO NOT contain search string
            'test': False, # make verbose output
            'append': False, 

        })

        # call constructor of the super class
        #super(BasicBot, self).__init__(site=True, **kwargs)
        super(BasicBot, self).__init__(**kwargs)

        # assign the generator to the bot
        self.generator = generator

    def run(self):

        header = u"last update: '''<onlyinclude>{{#time: Y-m-d H:i|{{REVISIONTIMESTAMP}}}}</onlyinclude>'''.\n\n"
        footer = u''

        #generate dictionary of articles
        # article[pl:title] = pageobject
        ceeArticles = self.getArticleList()
        self.printArtList(ceeArticles)

        pywikibot.output(u'ART INFO')
        count = 1
        for a in ceeArticles:
            aInfo = self.getArtInfo(a)
            if self.getOption('test'):
                pywikibot.output(aInfo)
            count += 1
            #populate article list per language
            if aInfo['lang'] not in self.springList.keys():
                self.springList[aInfo['lang']] = []
            self.springList[aInfo['lang']].append(aInfo)
            #populate authors list
            if aInfo['creator'] not in self.authors.keys():
                self.authors[aInfo['creator']] = 1
            else:
                self.authors[aInfo['creator']] += 1

        self.generateArticleList(self.springList,self.getOption('outpage')+u'/Article list',header,footer)
        self.generateAuthorsPage(self.authors,self.getOption('outpage')+u'/Authors list',header,footer)

        return

        #get template interwikis
        for p in self.generator:
            #p = t.toggleTalkPage()
            pywikibot.output(u'Treating: %s' % p.title())
            d = p.data_item()
            pywikibot.output(u'WD: %s' % d.title() )
            dataItem = d.get()
 
            for i in self.genInterwiki(p):
                lang = self.lang(i.title(asLink=True,forceInterwiki=True))
                #if lang not in ('be','pl'):
                #    continue
                self.templatesList[lang] = i.title()
                pywikibot.output(u'Getting references to %s Lang:%s' % (i.title(asLink=True,forceInterwiki=True), lang) )
                count = 0
                missing = 0
                articles = {}
                for p in i.getReferences(namespaces=1):
                    artParams = {}
                    art = p.toggleTalkPage()
                    count += 1
                    if art.exists():
                        #creator, creationDate = art.getCreator()
                        #pywikibot.output(u'%i:%s (Auth:%s, Created:%s)' % (count, art.title(asLink=True,forceInterwiki=True),creator, creationDate))
                        #count += 1
                        TmplInfo = self.getTemplateInfo(p, i.title(),lang)
                        creator, creationDate = art.getCreator()

                        artParams['template'] = TmplInfo
                        artParams['creator'] = creator
                        artParams['creationDate'] = creationDate
                        #print artParams

                        articles[art.title()] = artParams

                        author = u'[[:' + lang + u':user:' + creator + u'|' + lang + u':' + creator + u']]'

                        if creator in self.authors.keys():
                            self.authors[creator] +=1
                        else:
                            self.authors[creator] =1
                        #print (TmplInfo)
                    else:
                        missing += 1
                        pywikibot.output(u'Article referenced does not exist')
                self.springList[lang] = articles
                self.missingCount[lang] = missing
                self.pagesCount[lang] = count

                print(self.springList)
                print(self.authors)
                print(self.missingCount)
                print(self.pagesCount)
                print(self.women)

        self.generateresultspage(self.springList,self.getOption('outpage'),header,footer)
        return

    def getArticleList(self):
        #generate article list
        artList = []

        #use pagegenerator to get articles linking to CEE templates
        for p in self.generator:
            #p = t.toggleTalkPage()
            pywikibot.output(u'Treating: %s' % p.title())
            d = p.data_item()
            pywikibot.output(u'WD: %s' % d.title() )
            dataItem = d.get()
            count = 0
            for i in self.genInterwiki(p):
                lang = self.lang(i.title(asLink=True,forceInterwiki=True))
                #if lang not in ('crh'):
                #    continue
                self.templatesList[lang] = i.title()
                pywikibot.output(u'Getting references to %s Lang:%s' % (i.title(asLink=True,forceInterwiki=True), lang) )
                countlang = 0
                for p in i.getReferences(namespaces=1):
                    artParams = {}
                    art = p.toggleTalkPage()
                    if art.exists():
                        countlang += 1
                        artList.append(art)
                        if self.getOption('test'):
                            pywikibot.output(u'#%i/%i:%s:%s' % (count,countlang,lang,art.title()))
                        count += 1
        #get et.wiki article list
        if self.getOption('test'):
            pywikibot.output(u'GET ET WIKI')
        etwiki = pywikibot.Site('et',fam='wikipedia')
        etpage = pywikibot.Page( etwiki, 'Vikipeedia:Wikimedia CEE Spring 2017/Osalejad ja artiklid' )
        lang = self.lang(etpage.title(asLink=True,forceInterwiki=True))
        pywikibot.output(u'Getting links from %s Lang:%s' % (etpage.title(asLink=True,forceInterwiki=True), lang) )
        for p in etpage.linkedPages(namespaces=0):
            if p.exists():
                artList.append(p)
                if self.getOption('test'):
                     pywikibot.output(u'#%i:%s:%s' % (count,lang,p.title()))
                count += 1

        return(artList)

    def printArtList(self,artList):
        for p in artList:
            s = p.site
            l = s.code
            pywikibot.output(u'Page lang:%s : %s' % (l, p.title(asLink=True,forceInterwiki=True)))
        return

    def getArtInfo(self,art):
        #get article language, creator, creation date
        artParams = {}
        talk = art.toggleTalkPage()
        if art.exists():
            creator, creationDate = art.getCreator()
            lang = art.site.code
            
            artParams['title'] = art.title()
            artParams['lang'] = lang
            artParams['creator'] = creator
            artParams['creationDate'] = creationDate

            if lang in CEEtemplates.keys() and talk.exists():
                TmplInfo = self.getTemplateInfo(talk, CEEtemplates[lang], lang)
                artParams['template'] = TmplInfo

            #print artParams
        return(artParams)

    def getTemplateInfo(self,page,template,lang):
        param = {}
        #return dictionary with template params
        for t in page.templatesWithParams():
            title, params = t
            #print(title)
            #print(params)
            tt = re.sub(ur'\[\[.*?:(.*?)\]\]', r'\1', title.title())
            if self.getOption('test'):
                pywikibot.output(u'tml:%s = %s' % (title,template) )
            if tt == template:
                paramcount = 1
                for p in params:
                    named, name, value = self.templateArg(p)
                    if not named:
                        name = str(paramcount)
                    param[name] = value
                    paramcount += 1
                    if self.getOption('test'):
                        pywikibot.output(u'p:%s' % p )
                    #check parameter type: country, topic
                    if lang in self.topicp.keys() and name.lower().startswith(self.topicp[lang].lower()):
                        if self.getOption('test'):
                            pywikibot.output(u'topic:%s:%s' % (name,value))
                        if lang in self.womenp.keys() and value.lower().startswith(self.womenp[lang].lower()):
                            self.women[lang] += 1
                    if lang in self.countryp.keys() and name.lower().startswith(self.countryp[lang].lower()):
                        if self.getOption('test'):
                            pywikibot.output(u'country:%s:%s' % (name,value))
                return param
        return param

    def lang(self,template):
        return(re.sub(ur'\[\[(.*?):.*?\]\]',ur'\1',template))

    def genInterwiki(self,page):
        # yield interwiki sites generator
        iw = []
        try:
            d = page.data_item()
            pywikibot.output(u'WD: %s' % d.title() )
            dataItem = d.get()
            #pywikibot.output(u'DataItem:%s' % dataItem.keys()  )
            sitelinks = dataItem['sitelinks']
            for s in sitelinks:
                #if self.getOption('test'):
                #    pywikibot.output(u'SL iw: %s' % d)
                site = re.sub(ur'(.*)wiki$', ur'\1',s)
                if site == u'be_x_old':
                    site = u'be-tarask'
                ssite = pywikibot.Site(site,fam='wikipedia')
                spage = pywikibot.Page( ssite, title=sitelinks[s] )
                #pywikibot.output(u'gI Page: %s' % spage.title(asLink=True,forceInterwiki=True) )
                iw.append( spage )
                #print( iw)
        except:
            pass
        #print(iw)
        return(iw)

    def generateAuthorsPage(self, res, pagename, header, footer):
        """
        Generates results page from res
        Starting with header, ending with footer
        Output page is pagename
        """

        finalpage = header
        itemcount = 0
        finalpage += u'\n== Authors ==\n'
        #ath = sorted(self.authors, reverse=True)
        ath = sorted(res, key=res.__getitem__, reverse=True)
        for a in ath:
            finalpage += u'\n# ' + a + u' - ' + str(res[a])
            itemcount += 1

        finalpage += u'\n\nNumber of authors: ' + str(itemcount)
        finalpage += footer

        #pywikibot.output(finalpage)

        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if self.getOption('test'):
            pywikibot.output(u'AuthorsPage:%s' % outpage.title())
        outpage.text = finalpage
        outpage.save(summary=self.getOption('summary'))
        return

    def generateArticleList(self, res, pagename, header, footer):
        """
        Generates results page from res
        Starting with header, ending with footer
        Output page is pagename
        """

        finalpage = header

        itemcount = 0
        #go by language
        for l in res.keys():
            #print('[[:' + i + u':' + self.templatesList[i] +u'|' + i + u' wikipedia]]')
            if l in self.templatesList.keys():
                finalpage += u'\n== [[:' + l + u':Template:' + self.templatesList[l] +u'|' + l + u'.wikipedia]] ==\n\n'
            else:
                finalpage += u'\n== ' + l + u'.wikipedia ==\n\n'
            for i in res[l]:
                itemcount += 1
                finalpage += u'\n# [[:' + i['lang'] + u':' + i['title'] + u']] - user:' + i['creator'] + u' date:' + i['creationDate']
                if self.getOption('test'):
                    pywikibot.output(u'\n# [[:' + i['lang'] + u':' + i['title'] + u']] - user:' + i['creator'] + u' date:' + i['creationDate'])

        finalpage += u'\n\nTotal number of articles: ' + str(itemcount)
        finalpage += footer
        #pywikibot.output(finalpage)

        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if self.getOption('test'):
            pywikibot.output(u'ArticlesPage:%s' % outpage.title())
        outpage.text = finalpage        
        outpage.save(summary=self.getOption('summary'))
        return

    def generateresultspage(self, res, pagename, header, footer):
        """
        Generates results page from res
        Starting with header, ending with footer
        Output page is pagename
        """

        finalpage = header

        itemcount = 0
        for i in res.keys():
            count = 1
            #print('[[:' + i + u':' + self.templatesList[i] +u'|' + i + u' wikipedia]]')
            finalpage += u'\n== [[:' + i + u':' + self.templatesList[i] +u'|' + i + u' wikipedia]] ==\n\n'
            finalpage += u'Counted: ' + str(self.pagesCount[i]) + u' Missing:' + str(self.missingCount[i]) + u'\n\n'
            wiki = res[i]
            #print(wiki)
            for a in wiki.keys():
                finalpage += u'\n# [[:' + i + u':' + a + u']] - user:' + wiki[a]['creator'] + u' date:' + wiki[a]['creationDate']
                '''
                tmpl = wiki[a]['template']
                for p in tmpl.keys():
                    #print(p)
                    #print(tmpl[p])
                    finalpage += u',' + p + u'='
                    if tmpl[p]:
                        finalpage += tmpl[p]
                '''

        finalpage += u'\n== Authors ==\n'
        #ath = sorted(self.authors, reverse=True)
        ath = sorted(self.authors, key=self.authors.__getitem__, reverse=True)
        for a in ath:
             finalpage += u'\n# ' + a + u' - ' + str(self.authors[a])

        finalpage += u'\n== Articles about women ==\n'
        #ath = sorted(self.authors, reverse=True)
        wom = sorted(self.women, key=self.women.__getitem__, reverse=True)
        for a in self.women:
             finalpage += u'\n# ' + a + u' - ' + str(self.women[a])


        finalpage += footer 

        #pywikibot.output(finalpage)
        success = True
        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if self.getOption('append'):
            outpage.text += finalpage
        else:
            outpage.text = finalpage

        pywikibot.output(outpage.title())
        
        outpage.save(summary=self.getOption('summary'))
        #if not outpage.save(finalpage, outpage, self.summary):
        #   pywikibot.output(u'Page %s not saved.' % outpage.title(asLink=True))
        #   success = False
        return(success)


    def treat_page(self):
        """Load the given page, do some changes, and save it."""
        text = self.current_page.text

        ################################################################
        # NOTE: Here you can modify the text in whatever way you want. #
        ################################################################

        # If you find out that you do not want to edit this page, just return.
        # Example: This puts Text on a page.

        # Retrieve your private option
        # Use your own text or use the default 'Test'
        text_to_add = self.getOption('text')

        if self.getOption('replace'):
            # replace the page text
            text = text_to_add

        elif self.getOption('top'):
            # put text on top
            text = text_to_add + text

        else:
            # put text on bottom
            text += text_to_add

        # if summary option is None, it takes the default i18n summary from
        # i18n subdirectory with summary_key as summary key.
        self.put_current(text, summary=self.getOption('summary'))

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
        if self.getOption('test'):
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
