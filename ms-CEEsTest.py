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
from datetime import datetime

from pywikibot.bot import (
    MultipleSitesBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)
    #SingleSiteBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)
from pywikibot.tools import issue_deprecation_warning

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}
CEEtemplates = {'pl' : 'Szablon:CEE Spring 2017', 'az' : 'Şablon:Vikibahar 2017', 'ba' : 'Ҡалып:Вики-яҙ 2017', 'be' : 'Шаблон:CEE Spring 2017', 'Be-tarask' : 'Шаблён:Артыкул ВікіВясны-2017', 'bg' : 'Шаблон:CEE Spring 2017', 'de' : 'Vorlage:CEE_Spring_2017', 'crh' : 'Şablon:CEE Spring 2017', 'el' : 'Πρότυπο:CEE Spring 2017', 'myv' : 'ЛопаПарцун:ВикиТундо 2017', 'eo' : 'Ŝablono:Viki-printempo 2017', 'hy' : 'Կաղապար:CEE Spring 2017/հոդված', 'ka' : 'თარგი:ვიკიგაზაფხული 2017', 'lv' : 'Veidne:CEE Spring 2017', 'lt' : 'Šablonas:VRE 2017', 'mk' : 'Шаблон:СИЕ Пролет 2017', 'ro' : 'Format:Wikimedia CEE Spring 2017', 'ru' : 'Шаблон:Вики-весна 2017', 'sq' : 'Stampa:CEE Spring 2017', 'sr' : 'Šablon:CEE Spring 2017', 'tt' : 'Калып:Вики-яз 2017', 'tr' : 'Şablon:Vikibahar 2017', 'uk' : 'Шаблон:CEE Spring 2017', 'hu' : 'Sablon:CEE Tavasz 2017' }
countryList =[ u'Albania', u'Armenia', u'Austria', u'Azerbaijan', u'Bashkortostan', u'Belarus', u'Bosnia and Herzegovina', u'Bulgaria', u'Crimean Tatars', u'Croatia', u'Czechia', u'Erzia', u'Esperanto', u'Estonia', u'Georgia', u'Greece', u'Hungary', u'Kazakhstan', u'Kosovo', u'Latvia', u'Lithuania', u'Macedonia', u'Moldova', u'Poland', u'Romania', u'Russia', u'Serbia', u'Slovakia', u'Turkey', u'Ukraine', u'Other' ]
countryNames = {
'pl':{ 'Albania':'Albania', 'Austria':'Austria', 'Azerbejdżan':'Azerbaijan', 'Baszkortostan':'Bashkortostan', 'Białoruś':'Belarus', 'Bułgaria':'Bulgaria', 'Armenia':'Armenia', 'Bośnia i Hercegowina':'Bosnia and Herzegovina', 'Erzja':'Erzia', 'Esperanto':'Esperanto', 'Estonia':'Estonia', 'Gruzja':'Georgia', 'Czechy':'Czechia', 'Chorwacja':'Croatia', 'Kosowo':'Kosovo', 'Tatarzy krymscy':'Crimean Tatars', 'Litwa':'Lithuania', 'Łotwa':'Latvia', 'Węgry':'Hungary', 'Macedonia':'Macedonia', 'Mołdawia':'Moldova', 'Polska':'Poland', 'Rosja':'Russia', 'Rumunia':'Romania', 'Republika Serbska':'Serbia', 'Serbia':'Serbia', 'Słowacja':'Slovakia', 'Turcja':'Turkey', 'Ukraina':'Ukraine', 'Grecja':'Greece', 'Kazachstan':'Kazakhstan', },
'az':{ 'Albaniya':'Albania', 'Avstriya':'Austria', 'Azərbaycan':'Azerbaijan', 'Başqırdıstan':'Bashkortostan', 'Belarus':'Belarus', 'Bolqarıstan':'Bulgaria', 'Ermənistan':'Armenia', 'Bosniya və Herseqovina':'Bosnia and Herzegovina', 'Erzya':'Erzia', 'Esperantida':'Esperanto', 'Estoniya':'Estonia', 'Gürcüstan':'Georgia', 'Çexiya':'Czechia', 'Xorvatiya':'Croatia', 'Kosovo':'Kosovo', 'Krımtatar':'Crimean Tatars', 'Krım tatarları':'Crimean Tatars', 'Krım-Tatar':'Crimean Tatars', 'Litva':'Lithuania', 'Latviya':'Latvia', 'Macarıstan':'Hungary', 'Makedoniya':'Macedonia', 'Moldova':'Moldova', 'Polşa':'Poland', 'Rusiya':'Russia', 'Rumıniya':'Romania', 'Serb Respublikası':'Serbia', 'Serbiya':'Serbia', 'Slovakiya':'Slovakia', 'Türkiyə':'Turkey', 'Ukrayna':'Ukraine', 'Yunanıstan':'Greece', 'Qazaxıstan':'Kazakhstan', },
'ba':{ 'Албания':'Albania', 'Австрия':'Austria', 'Әзербайжан':'Azerbaijan', 'Башҡортостан':'Bashkortostan', ' Белоруссия':'Belarus', 'Беларусь':'Belarus', 'Болгария':'Bulgaria', 'Әрмәнстан':'Armenia', 'Босния һәм Герцеговина':'Bosnia and Herzegovina', 'Эрзя':'Erzia', 'Эсперантида':'Esperanto', 'Эстония':'Estonia', 'Грузия':'Georgia', 'Чехия':'Czechia', 'Хорватия':'Croatia', 'Косово':'Kosovo', 'Ҡырым Республикаһы':'Crimean Tatars', 'Ҡырым татарҙары':'Crimean Tatars', 'Литва':'Lithuania', 'Латвия':'Latvia', 'Венгрия':'Hungary', 'Македония':'Macedonia', 'Молдавия':'Moldova', 'Польша':'Poland', 'Рәсәй':'Russia', 'Румыния':'Romania', 'Серб Республикаһы':'Serbia', 'Сербия':'Serbia', 'Словакия':'Slovakia', 'Төркиә':'Turkey', 'Украина':'Ukraine', 'Греция':'Greece', 'Ҡаҙағстан':'Kazakhstan', },
'be':{ 'Албанія':'Albania', 'Аўстрыя':'Austria', 'Азербайджан':'Azerbaijan', 'Башкартастан':'Bashkortostan', 'Беларусь':'Belarus', 'Балгарыя':'Bulgaria', 'Арменія':'Armenia', 'Боснія і Герцагавіна':'Bosnia and Herzegovina', 'Эрзя':'Erzia', 'Эсперанта':'Esperanto', 'Эстонія':'Estonia', 'Грузія':'Georgia', 'Чэхія':'Czechia', 'Харватыя':'Croatia', 'Рэспубліка Косава':'Kosovo', 'Крымскія татары':'Crimean Tatars', 'Літва':'Lithuania', 'Латвія':'Latvia', 'Венгрыя':'Hungary', 'Македонія':'Macedonia', 'Малдова':'Moldova', 'Польшча':'Poland', 'Расія':'Russia', 'Румынія':'Romania', 'Рэспубліка Сербская':'Serbia', 'Сербія':'Serbia', 'Славакія':'Slovakia', 'Турцыя':'Turkey', 'Украіна':'Ukraine', 'Грэцыя':'Greece', 'Казахстан':'Kazakhstan', },
'be-tarask':{ 'Альбанія':'Albania', 'Аўстрыя':'Austria', 'Азэрбайджан':'Azerbaijan', 'Башкартастан':'Bashkortostan', 'Беларусь':'Belarus', 'Баўгарыя':'Bulgaria', 'Армэнія':'Armenia', 'Босьнія і Герцагавіна':'Bosnia and Herzegovina', 'Эрзя':'Erzia', 'Эспэранта':'Esperanto', 'Эстонія':'Estonia', 'Грузія':'Georgia', 'Чэхія':'Czechia', 'Харватыя':'Croatia', 'Косава':'Kosovo', 'Крымскія татары':'Crimean Tatars', 'Летува':'Lithuania', 'Латвія':'Latvia', 'Вугоршчына':'Hungary', 'Македонія':'Macedonia', 'Малдова':'Moldova', 'Польшча':'Poland', 'Расея':'Russia', 'Румынія':'Romania', 'Рэспубліка Сэрбская':'Serbia', 'Сэрбія':'Serbia', 'Славаччына':'Slovakia', 'Турэччына':'Turkey', 'Украіна':'Ukraine', 'Грэцыя':'Greece', 'Казахстан':'Kazakhstan', },
'bg':{ 'Албания':'Albania', 'Австрия':'Austria', 'Азербайджан':'Azerbaijan', 'Башкортостан':'Bashkortostan', 'Беларус':'Belarus', 'България':'Bulgaria', 'Армения':'Armenia', 'Босна и Херцеговина':'Bosnia and Herzegovina', 'ерзяни':'Erzia','Эрзя':'Erzia', 'Есперанто':'Esperanto', 'Естония':'Estonia', 'Грузия':'Georgia', 'Чехия':'Czechia', 'Хърватия':'Croatia', 'Косово':'Kosovo', 'кримски татари':'Crimean Tatars', 'Кримски татари':'Crimean Tatars', 'Литва':'Lithuania', 'Латвия':'Latvia', 'Унгария':'Hungary', 'Република Македония':'Macedonia', 'Македония':'Macedonia', 'Молдова':'Moldova', 'Полша':'Poland', 'Русия':'Russia', 'Румъния':'Romania', 'Република Сръбска':'Serbia', 'Сърбия':'Serbia', 'Словакия':'Slovakia', 'Турция':'Turkey', 'Украйна':'Ukraine', 'Гърция':'Greece', 'Казахстан':'Kazakhstan', },
'de':{ 'Albanien':'Albania', 'Österreich':'Austria', 'Aserbaidschan':'Azerbaijan', 'Baschkortostan':'Bashkortostan', 'Weißrussland':'Belarus', 'Bulgarien':'Bulgaria', 'Armenien':'Armenia', 'Bosnien und Herzegowina':'Bosnia and Herzegovina', 'Ersja':'Erzia', 'Esperanto':'Esperanto', 'Estland':'Estonia', 'Georgien':'Georgia', 'Tschechien':'Czechia', 'Kroatien':'Croatia', 'Kosovo':'Kosovo', 'Krimtataren':'Crimean Tatars', 'Litauen':'Lithuania', 'Lettland':'Latvia', 'Ungarn':'Hungary', 'Mazedonien':'Macedonia', 'Moldawien':'Moldova', 'Polen':'Poland', 'Russland':'Russia', 'Rumänien':'Romania', 'Republika Srpska':'Serbia', 'Serbien':'Serbia', 'Slowakei':'Slovakia', 'Türkei':'Turkey', 'Ukraine':'Ukraine', 'Griechenland':'Greece', 'Kasachstan':'Kazakhstan', },
'crh':{ 'Arnavutlıq':'Albania', 'Avstriya':'Austria', 'Azerbaycan':'Azerbaijan', 'Başqırtistan':'Bashkortostan', 'Belarus':'Belarus', 'Bulğaristan':'Bulgaria', 'Ermenistan':'Armenia', 'Bosna ve Hersek':'Bosnia and Herzegovina', 'Esperanto':'Esperanto', 'Estoniya':'Estonia', 'Gürcistan':'Georgia', 'Çehiya':'Czechia', 'Hırvatistan':'Croatia', 'Kosovo':'Kosovo', 'Qırımtatarlar':'Crimean Tatars', 'Litvaniya':'Lithuania', 'Latviya':'Latvia', 'Macaristan':'Hungary', 'Makedoniya':'Macedonia', 'Moldova':'Moldova', 'Lehistan':'Poland', 'Rusiye':'Russia', 'Romaniya':'Romania', 'Sırb Cumhuriyeti':'Serbia', 'Sırbistan':'Serbia', 'Slovakiya':'Slovakia', 'Türkiye':'Turkey', 'Ukraina':'Ukraine', 'Yunanistan':'Greece', 'Qazahistan':'Kazakhstan', },
'el':{ 'Αλβανία':'Albania', 'Αυστρία':'Austria', 'Αζερμπαϊτζάν':'Azerbaijan', 'Μπασκορτοστάν':'Bashkortostan', 'Λευκορωσία':'Belarus', 'Βουλγαρία':'Bulgaria', 'Αρμενία':'Armenia', 'Βοσνία και Ερζεγοβίνη':'Bosnia and Herzegovina', 'Έρζυα':'Erzia', 'Εσπεράντο':'Esperanto', 'Εσθονία':'Estonia', 'Γεωργία':'Georgia', 'Τσεχία':'Czechia', 'Κροατία':'Croatia', 'Κόσοβο':'Kosovo', 'Τατάροι Κριμαίας':'Crimean Tatars', 'Λιθουανία':'Lithuania', 'Λετονία':'Latvia', 'Ουγγαρία':'Hungary', 'πΓΔΜ':'Macedonia', 'Μολδαβία':'Moldova', 'Πολωνία':'Poland', 'Ρωσία':'Russia', 'Ρουμανία':'Romania', 'Σερβική Δημοκρατία':'Serbia', 'Σερβία':'Serbia', 'Σλοβακία':'Slovakia', 'Τουρκία':'Turkey', 'Ουκρανία':'Ukraine', 'Ελλάδα':'Greece', 'Καζακστάν':'Kazakhstan', },
'myv':{ 'Албания':'Albania', 'Австрия':'Austria', 'Азербайджан':'Azerbaijan', 'Башкирия':'Bashkortostan', 'Белорузия':'Belarus', 'Болгария':'Bulgaria', 'Армения':'Armenia', 'Босния ды Герцеговина':'Bosnia and Herzegovina', 'Эрзя':'Erzia', 'Эсперанто':'Esperanto', 'Эстэнь':'Estonia', 'Грузия':'Georgia', 'Чехия':'Czechia', 'Хорватия':'Croatia', 'Литва':'Lithuania', 'Латвия':'Latvia', 'Мадьяронь':'Hungary', 'Македония':'Macedonia', 'Молдавия':'Moldova', 'Польша':'Poland', 'Россия':'Russia', 'Румыния':'Romania', 'Сербань Республикась':'Serbia', 'Сербия':'Serbia', 'Словакия':'Slovakia', 'Турция':'Turkey', 'Украина':'Ukraine', 'Греция':'Greece', 'Казахстан':'Kazakhstan', },
'eo':{ 'Albanio':'Albania', 'Aŭstrio':'Austria', 'Azerbajĝano':'Azerbaijan', 'Baŝkirio':'Bashkortostan', 'Belorusio':'Belarus', 'Bulgario':'Bulgaria', 'Armenio':'Armenia', 'Bosnio kaj Hercegovino':'Bosnia and Herzegovina', 'Erzja':'Erzia', 'Esperantujo':'Esperanto', 'Esperanto':'Esperanto', 'Estonio':'Estonia', 'Kartvelio':'Georgia', 'Ĉeĥio':'Czechia', 'Kroatio':'Croatia', 'Kosovo':'Kosovo', 'Krimeo':'Crimean Tatars', 'Krime-tataroj':'Crimean Tatars', 'Litovio':'Lithuania', 'Latvio':'Latvia', 'Hungario':'Hungary', 'Makedonio':'Macedonia', 'Moldava':'Moldova', 'Pollando':'Poland', 'Rusio':'Russia', 'Rumanio':'Romania', 'Serba Respubliko':'Serbia', 'Serbio':'Serbia', 'Slovakio':'Slovakia', 'Turkio':'Turkey', 'Ukrainio':'Ukraine', 'Grekio':'Greece', 'Kazaĥio':'Kazakhstan', },
'hy':{ 'Ալբանիա':'Albania', 'Ավստրիա':'Austria', 'Ադրբեջանական Հանրապետություն':'Azerbaijan', 'Բաշկորտոստան':'Bashkortostan', 'Բելառուս':'Belarus', 'Բուլղարիա':'Bulgaria', 'Հայաստան':'Armenia', 'Բոսնիա և Հերցեգովինա':'Bosnia and Herzegovina', 'Էսպերանտո':'Esperanto', 'Էստոնիա':'Estonia', 'Վրաստան':'Georgia', 'Չեխիա':'Czechia', 'Խորվաթիա':'Croatia', 'Կոսովո':'Kosovo', 'Ղրիմի թաթարներ':'Crimean Tatars', 'Լիտվա':'Lithuania', 'Լատվիա':'Latvia', 'Հունգարիա':'Hungary', 'Մակեդոնիայի Հանրապետություն':'Macedonia', 'Մոլդովա':'Moldova', 'Լեհաստան':'Poland', 'Ռուսաստան':'Russia', 'Ռումինիա':'Romania', 'Սերբական Հանրապետություն':'Serbia', 'Սերբիա':'Serbia', 'Սլովակիա':'Slovakia', 'Թուրքիա':'Turkey', 'Ուկրաինա':'Ukraine', 'Հունաստան':'Greece', 'Ղազախստան':'Kazakhstan', },
'ka':{ 'ალბანეთი':'Albania', 'ავსტრია':'Austria', 'აზერბაიჯანი':'Azerbaijan', 'ბაშკირეთი':'Bashkortostan', 'ბელარუსი':'Belarus', 'ბულგარეთი':'Bulgaria', 'სომხეთი':'Armenia', 'ბოსნია და ჰერცეგოვინა':'Bosnia and Herzegovina', 'ესპერანტო':'Esperanto', 'ესტონეთი':'Estonia', 'საქართველო':'Georgia', 'ჩეხეთი':'Czechia', 'ხორვატია':'Croatia', 'კოსოვო':'Kosovo', 'ყირიმელი თათრები':'Crimean Tatars', 'ლიტვა':'Lithuania', 'ლატვია':'Latvia', 'უნგრეთი':'Hungary', 'მაკედონია':'Macedonia', 'მოლდოვა':'Moldova', 'პოლონეთი':'Poland', 'რუსეთი':'Russia', 'რუმინეთი':'Romania', 'სერბთა რესპუბლიკა':'Serbia', 'სერბეთი':'Serbia', 'სლოვაკეთი':'Slovakia', 'თურქეთი':'Turkey', 'უკრაინა':'Ukraine', 'საბერძნეთი':'Greece', 'ყაზახეთი':'Kazakhstan', },
'lv':{ 'Albānija':'Albania', 'Austrija':'Austria', 'Azerbaidžāna':'Azerbaijan', 'Baškortostāna':'Bashkortostan', 'Baltkrievija':'Belarus', 'Bulgārija':'Bulgaria', 'Armēnija':'Armenia', 'Bosnija un Hercegovina':'Bosnia and Herzegovina', 'erzji':'Erzia', 'Erzju':'Erzia', 'Esperanto':'Esperanto', 'Igaunija':'Estonia', 'Gruzija':'Georgia', 'Čehija':'Czechia', 'Horvātija':'Croatia', 'Kosova':'Kosovo', 'Krimas tatāri':'Crimean Tatars', 'Lietuva':'Lithuania', 'Latvija':'Latvia', 'Ungārija':'Hungary', 'Maķedonija':'Macedonia', 'Moldova':'Moldova', 'Polija':'Poland', 'Krievija':'Russia', 'Rumānija':'Romania', 'Serbu Republika':'Serbia', 'Serbija':'Serbia', 'Slovākija':'Slovakia', 'Turcija':'Turkey', 'Ukraina':'Ukraine', 'Grieķija':'Greece', 'Kazahstāna':'Kazakhstan', },
'lt':{ 'Albanija':'Albania', 'Austrija':'Austria', 'Azerbaidžanas':'Azerbaijan', 'Baškirija':'Bashkortostan', 'Baltarusija':'Belarus', 'Bulgarija':'Bulgaria', 'Armėnija':'Armenia', 'Bosnija ir Hercegovina':'Bosnia and Herzegovina', 'Erzių':'Erzia', 'Esperanto':'Esperanto', 'Estija':'Estonia', 'Gruzija':'Georgia', 'Čekija':'Czechia', 'Kroatija':'Croatia', 'Kosovas':'Kosovo', 'Krymas':'Crimean Tatars', 'Krymo totoriai':'Crimean Tatars', 'Lietuva':'Lithuania', 'Latvija':'Latvia', 'Vengrija':'Hungary', 'Makedonija':'Macedonia', 'Moldavija':'Moldova', 'Lenkija':'Poland', 'Rusija':'Russia', 'Rumunija':'Romania', 'Serbų Respublika':'Serbia', 'Serbų respublika':'Serbia', 'Serbija':'Serbia', 'Slovakija':'Slovakia', 'Turkija':'Turkey', 'Ukraina':'Ukraine', 'Graikija':'Greece', 'Kazachstanas':'Kazakhstan', },
'mk':{ 'Албанија':'Albania', 'Австрија':'Austria', 'Азербејџан':'Azerbaijan', 'Bashkortostani':'Bashkortostan', 'Белорусија':'Belarus', 'Бугарија':'Bulgaria', 'Ерменија':'Armenia', 'Босна и Херцеговина':'Bosnia and Herzegovina', 'Ерзја':'Erzia', 'Есперанто':'Esperanto', 'Естонија':'Estonia', 'Грузија':'Georgia', 'Чешка':'Czechia', 'Хрватска':'Croatia', 'Косово':'Kosovo', 'Република Косово':'Kosovo', 'Кримски Татари':'Crimean Tatars', 'Литванија':'Lithuania', 'Латвија':'Latvia', 'Унгарија':'Hungary', 'Македонија':'Macedonia', 'Молдавија':'Moldova', 'Полска':'Poland', 'Русија':'Russia', 'Романија':'Romania', 'Република Српска':'Serbia', 'Србија':'Serbia', 'Словачка':'Slovakia', 'Турција':'Turkey', 'Украина':'Ukraine', 'Грција':'Greece', 'Казахстан':'Kazakhstan', },
'ro':{ 'Albania':'Albania', 'Austria':'Austria', 'Azerbaidjan':'Azerbaijan', 'Bașchiria':'Bashkortostan', 'Belarus':'Belarus', 'Bulgaria':'Bulgaria', 'Armenia':'Armenia', 'Bosnia și Herțegovina':'Bosnia and Herzegovina', 'Esperanto':'Esperanto', 'Estonia':'Estonia', 'Georgia':'Georgia', 'Cehia':'Czechia', 'Croația':'Croatia', 'Kosovo':'Kosovo', 'Crimeea':'Crimean Tatars', 'Lituania':'Lithuania', 'Letonia':'Latvia', 'Ungaria':'Hungary', 'Macedonia':'Macedonia', 'Republica Moldova':'Moldova', 'Polonia':'Poland', 'Rusia':'Russia', 'România':'Romania', 'Republika Srpska':'Serbia', 'Serbia':'Serbia', 'Slovacia':'Slovakia', 'Turcia':'Turkey', 'Ucraina':'Ukraine', 'Grecia':'Greece', 'Kazahstan':'Kazakhstan', 'Erzia':'Erzia'},
'ru':{ 'Албания':'Albania', 'Австрия':'Austria', 'Азербайджан':'Azerbaijan', 'Башкортостан':'Bashkortostan', 'Белоруссия':'Belarus', 'Болгария':'Bulgaria', 'Армения':'Armenia', 'Босния и Герцеговина':'Bosnia and Herzegovina', 'Эрзя':'Erzia', 'Эсперантида':'Esperanto', 'Эсперанто':'Esperanto', 'Эстония':'Estonia', 'Грузия':'Georgia', 'Чехия':'Czechia', 'Хорватия':'Croatia', 'Косово':'Kosovo', 'Крымские татары':'Crimean Tatars', 'Литва':'Lithuania', 'Латвия':'Latvia', 'Венгрия':'Hungary', 'Республика Македония':'Macedonia', 'Македония':'Macedonia', 'Молдавия':'Moldova', 'Польша':'Poland', 'Россия':'Russia', 'Румыния':'Romania', 'Сербская Республика':'Serbia', 'Республика Сербская':'Serbia', 'Сербия':'Serbia', 'Словакия':'Slovakia', 'Турция':'Turkey', 'Украина':'Ukraine', 'Греция':'Greece', 'Казахстан':'Kazakhstan', },
'sq':{ 'Shqipërisë':'Albania', 'Shqipëria':'Albania', 'Austria':'Austria', 'Azerbajxhanit':'Azerbaijan', 'Azerbajxhani':'Azerbaijan', 'Bashkortostani':'Bashkortostan', 'Bjellorusia':'Belarus', 'Bullgaria':'Bulgaria', 'Armenisë':'Armenia', 'Armenia':'Armenia', 'Bosnja dhe Hercegovina':'Bosnia and Herzegovina', 'Gjuha esperanto':'Esperanto', 'Estonia':'Estonia', 'Gjeorgjisë':'Georgia', 'Gjeorgjia':'Georgia', 'Republika Çeke':'Czechia', 'Kroacisë':'Croatia', 'Kroacia':'Croatia', 'Kosovës':'Kosovo', 'Kosova':'Kosovo', 'Lituania':'Lithuania', 'Letonia':'Latvia', 'Hungaria':'Hungary', 'Maqedonisë':'Macedonia', 'Moldavinë':'Moldova', 'Moldavia':'Moldova', 'Polonisë':'Poland', 'Polonia':'Poland', 'Rusisë':'Russia', 'Rusia':'Russia', 'Rumania':'Romania', 'Serbia':'Serbia', 'Sllovakia':'Slovakia', 'Turqisë':'Turkey', 'Turqia':'Turkey', 'Ukraina':'Ukraine', 'Greqisë':'Greece', 'Greqia':'Greece', 'Kazakistanin':'Kazakhstan', 'Kazakistani':'Kazakhstan', },
'sr':{ 'Албанија':'Albania', 'Аустрија':'Austria', 'Азербејџан':'Azerbaijan', 'Башкортостан':'Bashkortostan', 'Белорусија':'Belarus', 'Бугарска':'Bulgaria', 'Јерменија':'Armenia', 'Босна и Херцеговина':'Bosnia and Herzegovina', 'Ерзја':'Erzia', 'Есперанто':'Esperanto', 'Естонија':'Estonia', 'Грузија':'Georgia', 'Чешка':'Czechia', 'Хрватска':'Croatia', 'Република Косово':'Kosovo', 'Кримски Татари':'Crimean Tatars', 'Литванија':'Lithuania', 'Летонија':'Latvia', 'Мађарска':'Hungary', 'Република Македонија':'Macedonia', 'Молдавија':'Moldova', 'Пољска':'Poland', 'Русија':'Russia', 'Румунија':'Romania', 'Република Српска':'Serbia', 'Србија':'Serbia', 'Словачка':'Slovakia', 'Турска':'Turkey', 'Украјина':'Ukraine', 'Грчка':'Greece', 'Казахстан':'Kazakhstan', },
'tt':{ 'Албания':'Albania', 'Австрия':'Austria', 'Азәрбайҗан':'Azerbaijan', 'Башкортстан':'Bashkortostan', 'Беларусия':'Belarus', 'Болгария':'Bulgaria', 'Әрмәнстан':'Armenia', 'Босния һәм Герцеговина':'Bosnia and Herzegovina', 'Эрзя':'Erzia', 'Ирзә':'Erzia', 'Эсперанто':'Esperanto', 'Эстония':'Estonia', 'Гөрҗистан':'Georgia', 'Чехия':'Czechia', 'Хорватия':'Croatia', 'Косово Җөмһүрияте':'Kosovo', 'Кырым татарлары':'Crimean Tatars', 'Литва':'Lithuania', 'Latviä':'Latvia', 'Маҗарстан':'Hungary', 'Македония Җөмһүрияте':'Macedonia', 'Македония':'Macedonia', 'Молдова':'Moldova', 'Польша':'Poland', 'РФ':'Russia', 'Русия':'Russia', 'Румыния':'Romania', 'Сербия':'Serbia', 'Словакия':'Slovakia', 'Төркия':'Turkey', 'Украина':'Ukraine', 'Греция':'Greece', 'Казакъстан':'Kazakhstan', },
'tr':{ 'Arnavutluk':'Albania', 'Avusturya':'Austria', 'Azerbaycan':'Azerbaijan', 'Başkurdistan':'Bashkortostan', 'Beyaz Rusya':'Belarus', 'Bulgaristan':'Bulgaria', 'Ermenistan':'Armenia', 'Bosna-Hersek':'Bosnia and Herzegovina', 'Erzya':'Erzia', 'Esperanto':'Esperanto', 'Estonya':'Estonia', 'Gürcistan':'Georgia', 'Çek Cumhuriyeti':'Czechia', 'Hırvatistan':'Croatia', 'Kosova':'Kosovo', 'Kırım Tatar':'Crimean Tatars', 'Kırım Tatarları':'Crimean Tatars', 'Litvanya':'Lithuania', 'Letonya':'Latvia', 'Macaristan':'Hungary', 'Makedonya':'Macedonia', 'Moldova':'Moldova', 'Polonya':'Poland', 'Rusya':'Russia', 'Romanya':'Romania', 'Sırp Cumhuriyeti':'Serbia', 'Sırbistan':'Serbia', 'Slovakya':'Slovakia', 'Türkiye':'Turkey', 'Ukrayna':'Ukraine', 'Yunanistan':'Greece', 'Kazakistan':'Kazakhstan', },
'uk':{ 'Албанія':'Albania', 'Австрія':'Austria', 'Азербайджан':'Azerbaijan', 'Башкортостан':'Bashkortostan', 'Білорусь':'Belarus', 'Болгарія':'Bulgaria', 'Вірменія':'Armenia', 'Боснія і Герцеговина':'Bosnia and Herzegovina', 'Ерзя':'Erzia', 'Есперантида':'Esperanto', 'Есперанто':'Esperanto', 'Естонія':'Estonia', 'Грузія':'Georgia', 'Чехія':'Czechia', 'Хорватія':'Croatia', 'Косово':'Kosovo', 'Кримські татари':'Crimean Tatars', 'Литва':'Lithuania', 'Латвія':'Latvia', 'Угорщина':'Hungary', 'Македонія':'Macedonia', 'Молдова':'Moldova', 'Польща':'Poland', 'Росія':'Russia', 'Румунія':'Romania', 'Республіка Сербська':'Serbia', 'Сербія':'Serbia', 'Словаччина':'Slovakia', 'Туреччина':'Turkey', 'Україна':'Ukraine', 'Греція':'Greece', 'Казахстан':'Kazakhstan', },
'hu':{ 'Albánia':'Albania', 'Ausztria':'Austria', 'Azerbajdzsán':'Azerbaijan', 'Baskirföld':'Bashkortostan', 'Belorusz':'Belarus', 'Bulgária':'Bulgaria', 'Örményország':'Armenia', 'Bosznia és Hercegovina':'Bosnia and Herzegovina', 'Eszperantó':'Esperanto', 'Észtország':'Estonia', 'Grúzia':'Georgia', 'Csehország':'Czechia', 'Horvátország':'Croatia', 'Koszovo':'Kosovo', 'Krími tatárok':'Crimean Tatars', 'Litvánia':'Lithuania', 'Lettország':'Latvia', 'Magyarország':'Hungary', 'Macedónia':'Macedonia', 'Moldávia':'Moldova', 'Lengyelország':'Poland', 'Oroszország':'Russia', 'Románia':'Romania', 'Boszniai Szerb Köztársaság':'Serbia', 'Szerbia':'Serbia', 'Szlovákia':'Slovakia', 'Törökország':'Turkey', 'Ukrajna':'Ukraine', 'Görögország':'Greece', 'Kazahsztán':'Kazakhstan', },
'kk':{ 'Албания':'Albania', 'Аустрия':'Austria', 'Әзірбайжан':'Azerbaijan', 'Башқұртстан':'Bashkortostan', 'Беларусь':'Belarus', 'Болгария':'Bulgaria', 'Армения':'Armenia', 'Босния және Герцеговина':'Bosnia and Herzegovina', 'Эсперанто':'Esperanto', 'Эстония':'Estonia', 'Грузия':'Georgia', 'Чехия':'Czechia', 'Хорватия':'Croatia', 'Косово':'Kosovo', 'Қырым татарлары':'Crimean Tatars', 'Литва':'Lithuania', 'Латвия':'Latvia', 'Мажарстан':'Hungary', 'Македония':'Macedonia', 'Молдова':'Moldova', 'Польша':'Poland', 'Ресей':'Russia', 'Румыния':'Romania', 'Сербия':'Serbia', 'Словакия':'Slovakia', 'Түркия':'Turkey', 'Украина':'Ukraine', 'Грекия':'Greece', 'Қазақстан':'Kazakhstan', },
'et':{ 'Albaania':'Albania', 'Austria':'Austria', 'Aserbaidžaan':'Azerbaijan', 'Baškortostan':'Bashkortostan', 'Valgevene':'Belarus', 'Bulgaaria':'Bulgaria', 'Armeenia':'Armenia', 'Bosnia ja Hertsegoviina':'Bosnia and Herzegovina', 'Esperanto':'Esperanto', 'Eesti':'Estonia', 'Gruusia':'Georgia', 'Tšehhi':'Czechia', 'Horvaatia':'Croatia', 'Kosovo':'Kosovo', 'Krimski Tatari':'Crimean Tatars', 'Leedu':'Lithuania', 'Läti':'Latvia', 'Ungari':'Hungary', 'Makedoonia':'Macedonia', 'Moldova':'Moldova', 'Poola':'Poland', 'Venemaa':'Russia', 'Rumeenia':'Romania', 'Republika Srpska':'Serbia', 'Serbia':'Serbia', 'Slovakkia':'Slovakia', 'Türgi':'Turkey', 'Ukraina':'Ukraine', 'Kreeka':'Greece', 'Kasahstan':'Kazakhstan', 'Ersa':'Erzia'},
'hr':{ 'Albanija':'Albania', 'Austrija':'Austria', 'Azerbajdžan':'Azerbaijan', 'Baškirska':'Bashkortostan', 'Bjelorusija':'Belarus', 'Bugarska':'Bulgaria', 'Armenija':'Armenia', 'Bosna i Hercegovina':'Bosnia and Herzegovina', 'Esperanto':'Esperanto', 'Estonija':'Estonia', 'Gruzija':'Georgia', 'Češka':'Czechia', 'Hrvatska':'Croatia', 'Kosovo':'Kosovo', 'Krimski Tatari':'Crimean Tatars', 'Litva':'Lithuania', 'Latvija':'Latvia', 'Mađarska':'Hungary', 'Makedonija':'Macedonia', 'Moldavija':'Moldova', 'Poljska':'Poland', 'Rusija':'Russia', 'Rumunjska':'Romania', 'Republika Srpska':'Serbia', 'Srbija':'Serbia', 'Slovačka':'Slovakia', 'Turska':'Turkey', 'Ukrajina':'Ukraine', 'Grčka':'Greece', 'Kazahstan':'Kazakhstan', 'Erzya':'Erzia'},
}
etArticles = {'Chocimsk':'','Chocimski rajoon':'','Emilia Plater':'','Bánov':'','Nezdenice':'','Aleksotase vald':'','Centrase vald':'','Dainava vald':'','Eiguliai vald':'','Gričiupise vald':'','Panemunė vald':'','Petrašiūnai vald':'','Šančiai vald':'','Šilainiai vald':'','Žaliakalnise vald':'','Vilijampolė vald':'','Pačeriaukštė I':'','Parovėja':'','Likėnai':'','Kazliškis':'','Kriaunos':'','Karsakiškis':'','Dainava':'','Gričiupis':'','Palemonas':'','Amaliai':'','Naujasodis':'','Pažaislis':'','Petrašiūnai':'','Rambynas':'','Brenguļi vald':'','Trikāta vald':'','Kauguri vald':'','Trikāta':'','Brenguļi':'','Grundzāle vald':'','Aumeisteri mõis':'','Bilska vald':'','Palsmane vald':'','Variņi vald':'','Blome vald':'','Branti vald':'','Launkalne vald':'','Smiltene vald':'','Kalnamuiža':'','Smiltene mõis':'','Łoša (Minski oblast)':'','Vusa':'','Uša (Nemunas)':'','Usa jõgi':'',':lv:Pociems (stacija)':'','Agrolinnake':'','Třebenice':'','Štiavnica mäestik':'','Kalnujai':'','Vičiūnai':'','Rokai':'','Vaišvydava':'','Panemunė (Kaunas)':'','Kalniečiai':'','Žaliakalnis':'','Eiguliai kalmistu':'','Izmir Smajlaj':'Albaania','Amel Tuka':'Bosnia ja Hertsegoviina','Gabriela Petrova':'Bulgaaria','Aleksandr Šaronov':'Ersa','Laša Talahhadze':'Gruusia','Sara Kolak':'Horvaatia','Olga Rõpakova':'Kasahstan','Majlinda Kelmendi':'Kosovo','Kyriákos Ioánnou':'Küpros','Laura Ikauniece-Admidiņa':'Läti','Vadims Vasiļevskis':'','Mogamed Ibragimov':'Makedoonia','Libor Charfreitag':'Slovakkia','Primož Kozmus':'Sloveenia','Jan Kudlička':'Tšehhi','Áron Szilágyi':'Ungari','Iłona Usovič':'Valgevene','Ekateríni Stefanídi':'Kreeka','Nikoléta Kiriakopoúlou':'Kreeka','Paraskeví Papahrístou':'Kreeka','Ivana Španović':'Serbia','SunStroke Project':'Moldova','Sergei Polunin':'Ukraina','Deniss Vasiļjevs':'Läti','Pažaislise klooster':'Leedu','Poola-Türgi sõda (1672–1676)':'Poola','Natalia Jaresko':'Ukraina','Oleksandr Danõljuk':'Ukraina','Vladimir Suure mälestusmärk':'Ukraina','Jadranka Joksimović':'Serbia','Jaroslavli Riiklik Pedagoogikaülikool':'Venemaa','Arkadi Dvorkovitš':'Venemaa','Konstantin Ušinski':'Venemaa','Talat Xhaferi':'Makedoonia','Nikola Poposki':'Makedoonia','Nikola Popovski':'Makedoonia','Jana Burčeska':'Makedoonia','Comrati Riiklik Ülikool':'Moldova','Andrej Plenković':'Horvaatia','Artsvik':'Armeenia','Diana Hacıyeva':'Aserbaidžaan','Nathan Trent':'Austria','Adnan Terzić':'Bosnia ja Hertsegoviina','Anton Rop':'Sloveenia','Pauls Stradiņš':'Läti','Ivan Pilný':'Tšehhi','Stepan Erzia':'Ersa','Lituanica SAT-1':'Leedu','Kruonise hüdroakumulatsioonijaam':'Leedu','Elektrėnai Elektrijaam':'Leedu','Ventspilsi Raadioastronoomiakeskus':'Läti','Ksamili saared':'Albaania','Sisian':'Armeenia','Bakuu Kristallhall':'Aserbaidžaan','Šaršau':'Baškortostan','Bosnalijek':'Bosnia ja Hertsegoviina','Mustafa paša sild':'Bulgaaria','Vardzia':'Gruusia','Vennad Karusüdamed':'Eesti','Jalgat':'Ersa','Zofia Zamenhof':'Esperanto','Eurodom Osijek':'Horvaatia','Kasahstani pealinn':'Kasahstan','Mamuša':'Kosovo','Ohi päev':'Kreeka','Perekop':'Krimski Tatari','Asveja (järv Leedus)':'Leedu','Kuldīga tellissild':'Läti','Suur vesi':'Makedoonia','Radan':'Serbia','Topologi viadukt':'Rumeenia','Redžep-paša torn':'Republika Srpska','Dobšinská jääkoobas':'Slovakkia','Karla kraater':'Tatarstan','Baksı muuseum':'Türgi','Łahojski meteoriidikraater':'Valgevene','Arvils Ašeradens':'Läti','Göd':'Ungari','Szarvas':'Ungari','Tóthfalu':'Serbia','Lobnja':'Venemaa','Georgi Gretško':'Venemaa','Lubań (Poola)':'Poola','Anastasija Sevastova':'Läti','Aleksandrs Čaks':'Läti','Makedoonia denaar':'Makedoonia','Rodniki':'Venemaa','Ivan Makarov':'Eesti','Constanța Casino':'Rumeenia','Vasile Milea':'Rumeenia','Kadri Hazbiu':'Albaania','Pál Losonczi':'Ungari','Jarosław Iwaszkiewicz':'Poola','Ilze Indrāne':'Läti','Antonín Zápotocký':'Tšehhi','Arkadi Perventsev':'Venemaa','Karl Erjavec':'Sloveenia','Skënder Hyseni':'Kosovo'}
hrArticles = {'Erzjanski jezik':'Erzya', 'Alatjir (rijeka)':'Rusija', 'Villa Koliba':'Poljska', 'Bogorodica (himan)':'Poljska', 'Promet Bosne i Hercegovine':'Bosna i Hercegovina', 'Kolo (ples)':'Republika Srpska', 'Sarajevski progon Srba 1914.':'Bosna i Hercegovina', 'Halil Inalcik':'Turska', 'Tubetejka':'Tatarstan', 'Podzemna željeznica Samara':'Rusija', 'Podzemna željeznica Ekaterinburg':'Rusija', 'Podzemna željeznica Nižnji Novgorod':'Rusija', 'Podzemna željeznica Novosibirsk':'Rusija', 'Podzemna željeznica Kazanj':'Rusija', 'Struške večeri poezije':'Makedonija', 'HK Slovan Bratislava':'Slovačka', 'Peter Machajdik':'Slovačka', 'Aleko Konstantinov':'Bugarska', 'Predsjednik Kosova':'Kosovo', 'Stanovništvo Kosova':'Kosovo', 'Krimska Narodna Republika':'Tatarstan', 'Magnit':'Rusija', 'Aleksandra Herasimenja':'Bjelorusija', 'Birač (BIH)':'Bosna i Hercegovina', 'Hercegovački ustanak (1875.-1878.)':'Republika Srpska', 'Andrićgrad':'Republika Srpska', 'Kuršumli han':'Makedonija', 'Karusaru':'Estonija', 'Kuremaa':'Estonija', 'Mullutu-Suurlahi':'Estonija', 'Narva rezervoar':'Estonija', 'Paunkula rezervoar':'Estonija', 'Veisjaru':'Estonija', 'Eczabibasi Vitra':'Turska', 'Palatinos (jezero)':'Mađarska', 'Morskie Oko':'Poljska', 'RK Vardar':'Makedonija', 'Asveja (jezero)':'Litva', 'Plateliai (jezero)':'Litva', 'Nevežis (rijeka)':'Litva', 'Alania':'Gruzija', 'Inguri (rijeka)':'Gruzija', 'Tblisi (jezero)':'Gruzija', 'Giorgi Dvali':'Gruzija', 'Nicholas Marr':'Gruzija', 'Naviband':'Bjelorusija', 'Njemačka okupacija Bjelorusije u Drugom svjetskom ratu':'Bjelorusija'}
etAuthors = { 'Chocimsk':'Melilac', 'Chocimski rajoon':'Melilac', 'Emilia Plater':'Melilac', 'Bánov':'Melilac', 'Nezdenice':'Melilac', 'Aleksotase vald':'Melilac', 'Centrase vald':'Melilac', 'Dainava vald':'Melilac', 'Eiguliai vald':'Melilac', 'Gričiupise vald':'Melilac', 'Panemunė vald':'Melilac', 'Petrašiūnai vald':'Melilac', 'Šančiai vald':'Melilac', 'Šilainiai vald':'Melilac', 'Žaliakalnise vald':'Melilac', 'Vilijampolė vald':'Melilac', 'Pačeriaukštė I':'Melilac', 'Parovėja':'Melilac', 'Likėnai':'Melilac', 'Kazliškis':'Melilac', 'Kriaunos':'Melilac', 'Karsakiškis':'Melilac', 'Dainava':'Melilac', 'Gričiupis':'Melilac', 'Palemonas':'Melilac', 'Amaliai':'Melilac', 'Naujasodis':'Melilac', 'Pažaislis':'Melilac', 'Petrašiūnai':'Melilac', 'Rambynas':'Melilac', 'Brenguļi vald':'Melilac', 'Trikāta vald':'Melilac', 'Kauguri vald':'Melilac', 'Trikāta':'Melilac', 'Brenguļi':'Melilac', 'Grundzāle vald':'Melilac', 'Aumeisteri mõis':'Melilac', 'Bilska vald':'Melilac', 'Palsmane vald':'Melilac', 'Variņi vald':'Melilac', 'Blome vald':'Melilac', 'Branti vald':'Melilac', 'Launkalne vald':'Melilac', 'Smiltene vald':'Melilac', 'Kalnamuiža':'Melilac', 'Smiltene mõis':'Melilac', 'Łoša (Minski oblast)':'Melilac', 'Vusa':'Melilac', 'Uša (Nemunas)':'Melilac', 'Usa jõgi':'Melilac',':lv:Pociems (stacija)':'Melilac', 'Agrolinnake':'Melilac', 'Třebenice':'Melilac', 'Štiavnica mäestik':'Melilac', 'Kalnujai':'Melilac', 'Vičiūnai':'Melilac', 'Rokai':'Melilac', 'Vaišvydava':'Melilac', 'Panemunė (Kaunas)':'Melilac', 'Kalniečiai':'Melilac', 'Žaliakalnis':'Melilac', 'Eiguliai kalmistu':'Melilac', 'Izmir Smajlaj':'Mona', 'Amel Tuka':'Mona', 'Gabriela Petrova':'Mona', 'Aleksandr Šaronov':'Mona', 'Laša Talahhadze':'Mona', 'Sara Kolak':'Mona', 'Olga Rõpakova':'Mona', 'Majlinda Kelmendi':'Mona', 'Kyriákos Ioánnou':'Mona', 'Laura Ikauniece-Admidiņa':'Mona', 'Vadims Vasiļevskis':'Mona', 'Mogamed Ibragimov':'Mona', 'Libor Charfreitag':'Mona', 'Primož Kozmus':'Mona', 'Jan Kudlička':'Mona', 'Áron Szilágyi':'Mona', 'Iłona Usovič':'Mona', 'Ekateríni Stefanídi':'Raamaturott', 'Nikoléta Kiriakopoúlou':'Raamaturott', 'Paraskeví Papahrístou':'Raamaturott', 'Ivana Španović':'Raamaturott', 'SunStroke Project':'Raamaturott', 'Sergei Polunin':'Sacerdos79', 'Deniss Vasiļjevs':'Sacerdos79', 'Pažaislise klooster':'Sacerdos79', 'Poola-Türgi sõda (1672–1676)':'Sacerdos79', 'Natalia Jaresko':'Juhan121', 'Oleksandr Danõljuk':'Juhan121', 'Vladimir Suure mälestusmärk':'Juhan121', 'Jadranka Joksimović':'Juhan121', 'Jaroslavli Riiklik Pedagoogikaülikool':'Juhan121', 'Arkadi Dvorkovitš':'Juhan121', 'Konstantin Ušinski':'Juhan121', 'Talat Xhaferi':'Juhan121', 'Nikola Poposki':'Juhan121', 'Nikola Popovski':'Juhan121', 'Jana Burčeska':'Juhan121', 'Comrati Riiklik Ülikool':'Juhan121', 'Andrej Plenković':'Juhan121', 'Artsvik':'Juhan121', 'Diana Hacıyeva':'Juhan121', 'Nathan Trent':'Juhan121', 'Adnan Terzić':'Juhan121', 'Anton Rop':'Juhan121', 'Pauls Stradiņš':'Juhan121', 'Ivan Pilný':'Juhan121', 'Stepan Erzia':'Juhan121', 'Lituanica SAT-1':'Jaanus.kalde', 'Kruonise hüdroakumulatsioonijaam':'Jaanus.kalde', 'Elektrėnai Elektrijaam':'Jaanus.kalde', 'Ventspilsi Raadioastronoomiakeskus':'Jaanus.kalde', 'Ksamili saared':'Maareti', 'Sisian':'Maareti', 'Bakuu Kristallhall':'Maareti', 'Šaršau':'Maareti', 'Bosnalijek':'Maareti', 'Mustafa paša sild':'Maareti', 'Vardzia':'Maareti', 'Vennad Karusüdamed':'Maareti', 'Jalgat':'Maareti', 'Zofia Zamenhof':'Maareti', 'Eurodom Osijek':'Maareti', 'Kasahstani pealinn':'Maareti', 'Mamuša':'Maareti', 'Ohi päev':'Maareti', 'Perekop':'Maareti', 'Asveja (järv Leedus)':'Maareti', 'Kuldīga tellissild':'Maareti', 'Suur vesi':'Maareti', 'Radan':'Maareti', 'Topologi viadukt':'Maareti', 'Redžep-paša torn':'Maareti', 'Dobšinská jääkoobas':'Maareti', 'Karla kraater':'Maareti', 'Baksı muuseum':'Maareti', 'Łahojski meteoriidikraater':'Maareti', 'Arvils Ašeradens':'Metsavend', 'Göd':'Metsavend', 'Szarvas':'Metsavend', 'Tóthfalu':'Metsavend', 'Lobnja':'Metsavend', 'Georgi Gretško':'Metsavend', 'Lubań (Poola)':'Metsavend', 'Anastasija Sevastova':'Metsavend', 'Aleksandrs Čaks':'Metsavend', 'Makedoonia denaar':'Metsavend', 'Rodniki':'Metsavend', 'Ivan Makarov':'Metsavend', 'Constanța Casino':'Merryapples', 'Vasile Milea':'Velirand', 'Kadri Hazbiu':'Velirand', 'Pál Losonczi':'Velirand', 'Jarosław Iwaszkiewicz':'Velirand', 'Ilze Indrāne':'Velirand', 'Antonín Zápotocký':'Velirand', 'Arkadi Perventsev':'Velirand', 'Karl Erjavec':'Velirand', 'Skënder Hyseni':'Velirand' }

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
    authorsData = {}
    missingCount = {}
    pagesCount = {}
    countryTable = {}
    otherCountriesList = {'pl':[], 'az':[], 'ba':[], 'be':[], 'be-tarask':[], 'bg':[], 'de':[], 'crh':[], 'el':[], 'myv':[], 'eo':[], 'hy':[], 'ka':[], 'lv':[], 'lt':[], \
             'mk':[], 'ro':[], 'ru':[], 'sq':[], 'sr':[], 'tt':[], 'tr':[], 'uk':[], 'hu':[]}
    women = {'pl':0, 'az':0, 'ba':0, 'be':0, 'be-tarask':0, 'bg':0, 'de':0, 'crh':0, 'el':0, 'myv':0, 'eo':0, 'hy':0, 'ka':0, 'lv':0, 'lt':0, \
             'mk':0, 'ro':0, 'ru':0, 'sq':0, 'sr':0, 'tt':0, 'tr':0, 'uk':0, 'hu':0}
    countryp = { 'pl':'kraj', 'az':'ölkə', 'ba':'ил', 'be':'краіна', 'Be-tarask':'краіна', 'bg':'държава', 'de':'land', 'crh':'memleket', 'el':'country', \
                 'myv':'мастор', 'eo':'country', 'ka':'ქვეყანა', 'lv':'valsts', 'lt':'šalis', 'mk':'земја', 'ro':'țară', 'ru':'страна', 'sq':'country', \
                 'sr':'држава', 'tt':'ил', 'tr':'ülke', 'uk':'країна' }
    topicp = {'pl':'parametr', 'az':'qadınlar', 'ba':'тема', 'be':'тэма', 'Be-tarask':'тэма', 'bg':'тема', 'de':'thema', 'crh':'mevzu', 'el':'topic', \
             'myv':'тема', 'eo':'topic', 'ka':'თემა', 'lv':'tēma', 'lt':'tema', 'mk':'тема', 'ro':'secțiune', 'ru':'тема', 'sq':'topic', 'sr':'тема', \
             'tt':'тема', 'tr':'konu', 'uk':'тема'}
    womenp = {'pl':'kobiety', 'az':'qadınlar', 'ba':'Ҡатын-ҡыҙҙар', 'be':'Жанчыны', 'Be-tarask':'жанчыны', 'bg':'жени', 'de':'Frauen','el':'γυναίκες', \
              'ka':'ქალები', 'lv':'Sievietes','mk':'Жени', 'ro':'Femei', 'ru':'женщины', 'sq':'Gratë', 'sr':'Жене', 'tt':'Хатын-кызлар', 'tr':'Kadın',\
               'uk':'жінки', 'hu':'nők'}
    userp = {'pl':'autor', 'az':'istifadəçi', 'ba':'ҡатнашыусы', 'be':'удзельнік', 'Be-tarask':'удзельнік', 'bg':'потребител', 'hu':'szerkesztő',\
             'de':'benutzer','crh':'qullanıcı','el':'user', 'myv':'сёрмадыця', 'eo':'user', 'ka':'მომხმარებელი', 'lv':'dalībnieks', 'lt':'naudotojas',\
             'mk':'корисник', 'ro':'utilizator', 'ru':'участник', 'sq':'user', 'sr':'корисник', 'tt':'кулланучы', 'tr':'kullanıcı', 'uk':'користувач' }

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
            'test2': False, # make verbose output
            'test3': False, # make verbose output
            'test4': False, # make verbose output
            'short': False, # make short run
            'append': False, 

        })

        # call constructor of the super class
        #super(BasicBot, self).__init__(site=True, **kwargs)
        super(BasicBot, self).__init__(**kwargs)

        # assign the generator to the bot
        self.generator = generator

    def run(self):

        header = u'{{Wikipedysta:Masti/CEE Spring 2017/Header}}\n\n'
        header += u"Last update: '''<onlyinclude>{{#time: Y-m-d H:i|{{REVISIONTIMESTAMP}}}}</onlyinclude>'''.\n\n"
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
            if aInfo['newarticle']:
                user = aInfo['creator']
                if aInfo['creator'] not in self.authors.keys():
                    self.authors[aInfo['creator']] = 1
                else:
                    self.authors[aInfo['creator']] += 1
            else:
                user = aInfo['template']['user']
                if aInfo['template']['user'] not in self.authors.keys():
                    self.authors[aInfo['template']['user']] = 1
                else:
                    self.authors[aInfo['template']['user']] += 1
            self.newbie(aInfo['lang'],user)


        self.printArtInfo(self.springList)
        #print self.springList

        self.createCountryTable(self.springList) #generate results for pages about countries 
        self.createWomenTable(self.springList) #generate results for pages about women

        self.generateOtherCountriesTable(self.otherCountriesList,self.getOption('outpage')+u'/Other countries',header,footer)
        self.generateResultCountryTable(self.countryTable,self.getOption('outpage'),header,footer)
        self.generateResultArticleList(self.springList,self.getOption('outpage')+u'/Article list',header,footer)
        self.generateResultAuthorsPage(self.authors,self.getOption('outpage')+u'/Authors list',header,footer)
        self.generateResultWomenPage(self.women,self.getOption('outpage')+u'/Articles about women',header,footer)

        return


    def newbie(self,lang,user):
        #check if user is a newbie
        newbieLimit =  datetime.strptime("2016-12-20T12:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
        if user in self.authorsData.keys():
            if lang not in self.authorsData[user]['wikis']:
                self.authorsData[user]['wikis'].append(lang)
            if self.authorsData[user]['anon']:
                return(False)
            if not self.authorsData[user]['newbie']:
                return(False)
        else:
            self.authorsData[user] = {'newbie':True, 'wikis':[lang], 'anon':False, 'gender':'unknown'}
        userpage = u'user:' + user
        site = pywikibot.Site(lang,fam='wikipedia')
        #page = pywikibot.Page(site,userpage)
        userdata = pywikibot.User(site,userpage)
        self.authorsData[user]['anon'] = userdata.isAnonymous()
        if self.authorsData[user]['anon']:
            return(False)
        usergender = userdata.gender()
        if not self.authorsData[user]['gender'] == 'female':
            self.authorsData[user]['gender'] = usergender
        if self.authorsData[user]['newbie']:
            reg = userdata.registration()
            if reg:
                register = datetime.strptime(str(reg), "%Y-%m-%dT%H:%M:%SZ")
                if register < newbieLimit:
                    self.authorsData[user]['newbie'] = False

        return(self.authorsData[user]['newbie'])

    def createCountryTable(self,aList):
        #creat dictionary with la:country article counts
        if self.getOption('test2'):
            pywikibot.output(u'createCountryTable')
        artCount = 0
        countryCount = 0
        for l in aList.keys():
            for a in aList[l]:
                #print a
                artCount += 1
                lang = a['lang'] #source language
                tmpl = a['template'] #template data {country:[clist], women:T/F}
                if u'country' in tmpl.keys():
                    cList = tmpl['country']
                else:
                    continue
                if lang not in self.countryTable.keys():
                        self.countryTable[lang] = {}
                for c in cList:
                    if c not in self.countryTable[lang].keys():
                        self.countryTable[lang][c] = 0
                    self.countryTable[lang][c] += 1
                    countryCount += 1
                    if self.getOption('test'):
                        pywikibot.output(u'art:%i coutry:%i, [[%s:%s]]' % (artCount, countryCount, lang, a['title']))
        return

    def createWomenTable(self,aList):
        #creat dictionary with la:country article counts
        if self.getOption('test'):
            pywikibot.output(u'createWomenTable')
        artCount = 0
        countryCount = 0
        for l in aList.keys():
            for a in aList[l]:
                #print a
                artCount += 1
                lang = a['lang'] #source language
                tmpl = a['template'] #template data {country:[clist], women:T/F}
                if u'woman' in tmpl.keys():
                    if not tmpl['woman']:
                        continue
                else:
                    continue
                if lang not in self.women.keys():
                    self.women[lang] = 1
                else:
                    self.women[lang] += 1
                countryCount += 1
                if self.getOption('test'):
                    pywikibot.output(u'art:%i Women:True [[%s:%s]]' % (artCount, lang, a['title']))
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
                #test switch
                if self.getOption('short'):
                    if lang not in ('de'):
                         continue

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
        lang = u'et'
        for etart in etArticles.keys():
            etpage = pywikibot.Page( etwiki, etart )
            if etpage.exists():
                artList.append(etpage)
                if self.getOption('test'):
                     pywikibot.output(u'#%i:%s:%s' % (count,lang,etpage.title()))
                count += 1
        #get hr.wiki article list
        if self.getOption('test'):
            pywikibot.output(u'GET HR WIKI')
        hrwiki = pywikibot.Site('hr',fam='wikipedia')
        lang = u'hr'
        for hrart in hrArticles.keys():
            hrpage = pywikibot.Page( hrwiki, hrart )
            if hrpage.exists():
                artList.append(hrpage)
                if self.getOption('test'):
                     pywikibot.output(u'#%i:%s:%s' % (count,lang,hrpage.title()))
                count += 1

        return(artList)

    def printArtList(self,artList):
        for p in artList:
            s = p.site
            l = s.code
            if self.getOption('test'):
                pywikibot.output(u'Page lang:%s : %s' % (l, p.title(asLink=True,forceInterwiki=True)))
        return

    def printArtInfo(self,artInfo):
        #test print of article list result
        pywikibot.output(u'***************************************')
        pywikibot.output(u'**            artInfo                **')
        pywikibot.output(u'***************************************')
        for l in artInfo.keys():
            for a in artInfo[l]:
                pywikibot.output(a)
        return

    def getArtInfo(self,art):
        #get article language, creator, creation date
        artParams = {}
        talk = art.toggleTalkPage()
        if art.exists():
            creator, creationDate = self.getUpdater(art)
            lang = art.site.code

            woman = self.checkWomen(art)            
            artParams['title'] = art.title()
            artParams['lang'] = lang
            artParams['creator'] = creator
            artParams['creationDate'] = creationDate
            artParams['newarticle'] = self.newArticle(art)
            artParams['template'] = {u'country':[], 'user':creator, 'woman':woman}


            if lang in CEEtemplates.keys() and talk.exists():
                TmplInfo = self.getTemplateInfo(talk, CEEtemplates[lang], lang)
                artParams['template'] = TmplInfo
            if not artParams['template']['woman']:
                artParams['template']['woman'] = woman
            #hack for languages without templates
            countryEN = ''
            if lang == 'et':
                countryET = etArticles[artParams['title']]
                #if self.getOption('test2'):
                #    pywikibot.output(u'countryET:%s' % countryET)
                if countryET:
                    if countryET in countryNames['et'].keys():
                        countryEN = countryNames['et'][countryET]
                    else:
                        countryEN = countryET
                #if self.getOption('test2'):
                #    pywikibot.output(u'countryEN:%s' % countryEN)
                artParams['template'] = {'country':[countryEN], 'user':etAuthors[artParams['title']], 'woman':woman}
            if lang == 'hr':
                countryHR = hrArticles[artParams['title']]
                #if self.getOption('test2'):
                #    pywikibot.output(u'countryHR:%s' % countryHR)
                if countryHR:
                    if countryHR in countryNames['hr'].keys():
                        countryEN = countryNames['hr'][countryHR]
                    else:
                        countryEN = countryHR
                #if self.getOption('test2'):
                #    pywikibot.output(u'countryEN:%s' % countryEN)
                artParams['template'] = {'country':[countryEN], 'user':creator, 'woman':woman}
                if self.getOption('test2'):
                    pywikibot.output(u'artParams[template]:%s' % artParams['template'])

            if u'template' not in artParams.keys():
                artParams['template'] = {u'country':[], 'user':creator, 'woman':woman}
            if not artParams['newarticle'] : 
                artParams['template']['user'] = creator
                #artParams['creator'] = u'unknown'


            #print artParams
        return(artParams)

    def checkWomen(self,art):
        #check if the article is about woman 
        #using WikiData
        try:
            d = art.data_item()
            if self.getOption('test4'):
                pywikibot.output(u'WD: %s' % d.title() )
            dataItem = d.get()
            #pywikibot.output(u'DataItem:%s' % dataItem.keys()  )
            claims = dataItem['claims']
        except:
            return(False)
        try:
            gender = claims["P21"]
        except:
            return(False)
        for c in gender:
            cjson = c.toJSON()
            genderclaim = cjson[u'mainsnak'][u'datavalue'][u'value'][u'numeric-id']
            if u'6581072' == str(genderclaim):
                if self.getOption('test4'):
                    pywikibot.output(u'%s:Woman' % art.title())
                return(True)
            else:
                if self.getOption('test4'):
                    pywikibot.output(u'%s:Man' % art.title())
                return(False)
        return(False)

    def getUpdater(self, art):
        #find author and update datetime of the biggest update within CEESpring
        creator, creationDate = art.getCreator()
        SpringStart =  datetime.strptime("2017-03-20T12:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
        if self.newArticle(art):
            if self.getOption('test3'):
                pywikibot.output(u'New art creator %s:%s (T:%s)' % (art.title(asLink=True,forceInterwiki=True),creator,creationDate))
            return(creator, creationDate)
        else:
            #for rv in art.revisions(reverse=True,starttime="2017-03-20T12:00:00Z",endtime="2017-06-01T00:00:00Z"):
            for rv in art.revisions(reverse=True, starttime=SpringStart):
                if self.getOption('test3'):
                    pywikibot.output(u'updated art editor %s:%s (T:%s)' % (art.title(asLink=True,forceInterwiki=True),rv.user,rv.timestamp))
                if rv.timestamp > SpringStart:
                    return(rv.user,rv.timestamp)
                #if self.getOption('test3'):
                #    pywikibot.output(u'updated art editor %s:%s (T:%s)' % (art.title(asLink=True,forceInterwiki=True),rv['user'],rv['timestamp']))
            #    return(rv['user'],rv['timestamp'])
            return('unknown', creationDate)
       

    def newArticle(self,art):
        #check if the article was created within CEE Spring
        creator, creationDate = art.getCreator()
        SpringStart =  datetime.strptime("2017-03-20T12:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
        SpringEnd = datetime.strptime("2017-06-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
        return ( datetime.strptime(creationDate, "%Y-%m-%dT%H:%M:%SZ") > SpringStart )


    def getTemplateInfo(self,page,template,lang):
        param = {}
        author, creationDate = self.getUpdater(page)
        parlist = {'country':[],'user':author,'woman':False}
        #return dictionary with template params
        for t in page.templatesWithParams():
            title, params = t
            #print(title)
            #print(params)
            tt = re.sub(ur'\[\[.*?:(.*?)\]\]', r'\1', title.title())
            if self.getOption('test2'):
                pywikibot.output(u'tml:%s = %s = %s' % (title,tt,template) )
            if tt == template:
                paramcount = 1
                parlist['woman'] = False
                parlist['country'] = []
                parlist['user'] = author
                for p in params:
                    named, name, value = self.templateArg(p)
                    if not named:
                        name = str(paramcount)
                    param[name] = value
                    paramcount += 1
                    if self.getOption('test'):
                        pywikibot.output(u'p:%s' % p )
                    #check username in template
                    if lang in self.userp.keys() and name.lower().startswith(self.userp[lang].lower()):
                        if self.getOption('test'):
                            pywikibot.output(u'user:%s:%s' % (name,value))
                        #if lang in self.userp.keys() and value.lower().startswith(self.userp[lang].lower()):
                        #    parlist['user'] = value
                        parlist['user'] = value
                    #check article about women
                    if lang in self.topicp.keys() and name.lower().startswith(self.topicp[lang].lower()):
                        if self.getOption('test'):
                            pywikibot.output(u'topic:%s:%s' % (name,value))
                        if lang in self.womenp.keys() and value.lower().startswith(self.womenp[lang].lower()):
                            self.women[lang] += 1
                            parlist['woman'] = True
                    #check article about country
                    if lang in self.countryp.keys() and name.lower().startswith(self.countryp[lang].lower()):
                        if self.getOption('test2'):
                            pywikibot.output(u'country:%s:%s' % (name,value))
                        if len(value)>0:
                            if lang in countryNames.keys() and value in (countryNames[lang].keys()):
                                countryEN = countryNames[lang][value]
                                parlist['country'].append(countryEN)
                                if lang not in self.pagesCount.keys():
                                    self.pagesCount[lang] = {}
                                if countryEN in self.pagesCount[lang].keys():
                                    self.pagesCount[lang][countryEN] += 1
                                else:
                                    self.pagesCount[lang][countryEN] = 1
                            else:
                                parlist['country'].append(value)
                                self.otherCountriesList[lang].append(value)
                    if self.getOption('test'):
                        pywikibot.output(self.pagesCount)
                if self.getOption('test3'):
                    #pywikibot.output(u'PARAM:%s' % param)
                    pywikibot.output(u'PARLIST:%s' % parlist)
                return parlist
        return parlist

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

    def generateOtherCountriesTable(self, res, pagename, header, footer):
        """
        Generates results page from res
        Starting with header, ending with footer
        Output page is pagename
        """

        finalpage = header

        pywikibot.output(u'**************************')
        pywikibot.output(u'generateResultCountryTable')
        pywikibot.output(u'**************************')

        for c in self.otherCountriesList.keys():
            finalpage += u'\n== ' + c + u' =='
            for i in self.otherCountriesList[c]:
                finalpage += u'\n# <nowiki>' + i + u'</nowiki>'

        finalpage += footer
        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if self.getOption('test'):
            pywikibot.output(u'OtherCountries:%s' % outpage.title())
        outpage.text = finalpage
        outpage.save(summary=self.getOption('summary'))

        return


    def generateResultCountryTable(self, res, pagename, header, footer):
        """
        Generates results page from res
        Starting with header, ending with footer
        Output page is pagename
        """

        finalpage = header

        pywikibot.output(u'**************************')
        pywikibot.output(u'generateResultCountryTable')
        pywikibot.output(u'**************************')

        #total counters
        countryTotals = {}
        for c in countryList:
            countryTotals[c] = 0

        # generate table header
        finalpage += u'\n{| class="wikitable sortable" style="text-align: center;"'
        finalpage += u'\n|-'
        finalpage += u'\n! wiki/country'
        for c in countryList:
            finalpage += u' !! ' + c
        
        # generate table rows
        for wiki in res.keys():
            finalpage += u'\n|-'
            finalpage += u'\n| [[' + pagename + u'/Article list#'+ wiki + u'.wikipedia|' + wiki + u']]'
            for c in countryList:
                finalpage += u' || '
                if u'Other' in c:
                    if self.getOption('test3'):
                         pywikibot.output(u'other:%s' % c)
                         pywikibot.output(u'res[wiki]:%s' % res[wiki])
                    otherCountry = 0 # count other countries
                    for country in res[wiki]:
                       if country not in countryList and not country==u'':
                           if self.getOption('test3'):
                               pywikibot.output(u'country:%s ** otherCountry=%i+%i=%i' % (country,otherCountry,res[wiki][country],otherCountry+res[wiki][country]))
                           otherCountry += res[wiki][country]
                    finalpage += str(otherCountry)
                    countryTotals[c] += otherCountry
                else:
                    if c in res[wiki].keys():
                        if res[wiki][c]:
                            finalpage += str(res[wiki][c])
                            countryTotals[c] += res[wiki][c]
            
        finalpage += u'\n|-'

        # generate totals
        finalpage += u'\n! Total:'
        for c in countryList:
            finalpage += u' !! ' + str(countryTotals[c])
        # generate table footer
        finalpage += u'\n|}'

        finalpage += footer

        if self.getOption('test2'):
            pywikibot.output(finalpage)

        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if self.getOption('test'):
            pywikibot.output(u'WomenPage:%s' % outpage.title())
        outpage.text = finalpage
        outpage.save(summary=self.getOption('summary'))

        return

    def generateResultWomenPage(self, res, pagename, header, footer):
        """
        Generates results page from res
        Starting with header, ending with footer
        Output page is pagename
        """

        finalpage = header
        itemcount = 0
        finalpage += u'\n== Articles about women ==\n'
        #ath = sorted(self.authors, reverse=True)
        ath = sorted(res, key=res.__getitem__, reverse=True)
        for a in ath:
            finalpage += u'\n# ' + a + u' - ' + str(res[a])
            itemcount += res[a]

        finalpage += u'\n\nTotal number of articles: ' + str(itemcount)
        finalpage += footer

        #pywikibot.output(finalpage)

        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if self.getOption('test'):
            pywikibot.output(u'WomenPage:%s' % outpage.title())
        outpage.text = finalpage
        outpage.save(summary=self.getOption('summary'))
        return


    def generateResultAuthorsPage(self, res, pagename, header, footer):
        """
        Generates results page from res
        Starting with header, ending with footer
        Output page is pagename
        """

        finalpage = header
        itemcount = 0
        anon = 0
        women = 0
        newbies = 0
        finalpage += u'\n== Authors ==\n'
        #ath = sorted(self.authors, reverse=True)
        ath = sorted(res, key=res.__getitem__, reverse=True)
        for a in ath:
            if self.authorsData[a]['newbie']: 
                newbies += 1
            finalpage += u'\n# ' + a + u' - ' + str(res[a])
            if self.authorsData[a]['newbie']: 
                newbies += 1
                finalpage += u" - '''new editor'''"
            if self.authorsData[a]['gender'] == u'female': 
                women += 1
                finalpage += u" - '''female editor'''"
            if self.authorsData[a]['anon']:
                anon += 1 
            itemcount += 1

        finalpage += u'\n\nNumber of authors: ' + str(itemcount)
        finalpage += u'\n\nNumber of not registered authors: ' + str(anon)
        finalpage += u'\n\nNumber of female  authors: ' + str(women)
        finalpage += u'\n\nNumber of new authors: ' + str(newbies)

        finalpage += footer

        #pywikibot.output(finalpage)

        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if self.getOption('test'):
            pywikibot.output(u'AuthorsPage:%s' % outpage.title())
        outpage.text = finalpage
        outpage.save(summary=self.getOption('summary'))
        return

    def generateResultArticleList(self, res, pagename, header, footer):
        """
        Generates results page from res
        Starting with header, ending with footer
        Output page is pagename
        """

        finalpage = header
        
        itemcount = 0
        #go by language
        for l in res.keys():
            artCount = 0
            #print('[[:' + i + u':' + self.templatesList[i] +u'|' + i + u' wikipedia]]')
            if l in self.templatesList.keys():
                finalpage += u'\n== [[:' + l + u':Template:' + self.templatesList[l] +u'|' + l + u'.wikipedia]] =='
            else:
                finalpage += u'\n== ' + l + u'.wikipedia =='
            finalpage += u'\n=== ' + l + u'.wikipedia new articles ==='
            updatedArticles = u'\n\n=== ' + l + u'.wikipedia updated articles ==='
            for i in res[l]:
                itemcount += 1
                artCount += 1
                if i['newarticle']:
                    #finalpage += u' (NEW)'
                    #artLine = u'\n# [[:' + i['lang'] + u':' + i['title'] + u']] - user:' + i['creator'] + u' date:' + i['creationDate']
                    artLine = u'\n# [[:' + i['lang'] + u':' + i['title'] + u']] - user:' + i['creator']
                    for a in i['template']['country']:
                        if a in countryList:
                            artLine +=  u' - ' + a
                        else:
                            artLine +=  u" - '''" + a + u"'''"
                    finalpage += artLine
                    pywikibot.output(artLine + u' (NEW)')
                else:
                    #finalpage += u" '''(updated)'''"
                    if i['template']['user']:
                        artLine = u'\n# [[:' + i['lang'] + u':' + i['title'] + u']] - user:' + i['template']['user'] 
                    for a in i['template']['country']:
                        if a in countryList:
                            artLine +=  u' - ' + a
                        else:
                            artLine +=  u" - '''" + a + u"'''"
                    else:
                        artLine = u'\n# [[:' + i['lang'] + u':' + i['title'] + u']] - user:uknown'
                    for a in i['template']['country']:
                        if a in countryList:
                            artLine +=  u' - ' + a
                        else:
                            artLine +=  u" - '''" + a + u"'''"
                    updatedArticles += artLine
                    pywikibot.output(artLine + u" '''(updated)'''")

                #if self.getOption('test'):
                #    pywikibot.output(u'\n# [[:' + i['lang'] + u':' + i['title'] + u']] - user:' + i['creator'] + u' date:' + i['creationDate'])

            finalpage += updatedArticles
            finalpage += u'\nTotal number of articles:' + str(artCount)

        finalpage += u'\n\nTotal number of articles: ' + str(itemcount)
        finalpage += footer
        #pywikibot.output(finalpage)

        outpage = pywikibot.Page(pywikibot.Site(), pagename)
        if self.getOption('test'):
            pywikibot.output(u'ArticlesPage:%s' % outpage.title())
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
