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
countryNames = {
'pl':{ 'Albania':'Albania', 'Austria':'Austria', 'Azerbejdżan':'Azerbaijan', 'Baszkortostan':'Bashkortostan', 'Białoruś':'Belarus', 'Bułgaria':'Bulgaria', 'Armenia':'Armenia', 'Bośnia i Hercegowina':'Bosnia and Herzegovina', 'Erzja':'Erzia', 'Esperanto':'Esperanto', 'Estonia':'Estonia', 'Gruzja':'Georgia', 'Czechy':'Czechia', 'Chorwacja':'Croatia', 'Kosowo':'Kosovo', 'Tatarzy krymscy':'Crimean Tatars', 'Litwa':'Lithuania', 'Łotwa':'Latvia', 'Węgry':'Hungary', 'Macedonia':'Macedonia', 'Mołdawia':'Moldova', 'Polska':'Poland', 'Rosja':'Russia', 'Rumunia':'Romania', 'Republika Serbska':'Serbia', 'Serbia':'Serbia', 'Słowacja':'Slovakia ', 'Turcja':'Turkey', 'Ukraina':'Ukraine', 'Grecja':'Greece', 'Kazachstan':'Kazakhstan', },
'az':{ 'Albaniya':'Albania', 'Avstriya':'Austria', 'Azərbaycan':'Azerbaijan', 'Başqırdıstan':'Bashkortostan', 'Belarus':'Belarus', 'Bolqarıstan':'Bulgaria', 'Ermənistan':'Armenia', 'Bosniya və Herseqovina':'Bosnia and Herzegovina', 'Erzya':'Erzia', 'Esperantida':'Esperanto', 'Estoniya':'Estonia', 'Gürcüstan':'Georgia', 'Çexiya':'Czechia', 'Xorvatiya':'Croatia', 'Kosovo':'Kosovo', 'Krım-Tatar':'Crimean Tatars', 'Litva':'Lithuania', 'Latviya':'Latvia', 'Macarıstan':'Hungary', 'Makedoniya':'Macedonia', 'Moldova':'Moldova', 'Polşa':'Poland', 'Rusiya':'Russia', 'Rumıniya':'Romania', 'Serb Respublikası':'Serbia', 'Serbiya':'Serbia', 'Slovakiya':'Slovakia ', 'Türkiyə':'Turkey', 'Ukrayna':'Ukraine', 'Yunanıstan':'Greece', 'Qazaxıstan':'Kazakhstan', },
'ba':{ 'Албания':'Albania', 'Австрия':'Austria', 'Әзербайжан':'Azerbaijan', 'Башҡортостан':'Bashkortostan', 'Беларусь':'Belarus', 'Болгария':'Bulgaria', 'Әрмәнстан':'Armenia', 'Босния һәм Герцеговина':'Bosnia and Herzegovina', 'Эрзя':'Erzia', 'Эсперантида':'Esperanto', 'Эстония':'Estonia', 'Грузия':'Georgia', 'Чехия':'Czechia', 'Хорватия':'Croatia', 'Косово':'Kosovo', 'Ҡырым татарҙары':'Crimean Tatars', 'Литва':'Lithuania', 'Латвия':'Latvia', 'Венгрия':'Hungary', 'Македония':'Macedonia', 'Молдавия':'Moldova', 'Польша':'Poland', 'Рәсәй':'Russia', 'Румыния':'Romania', 'Серб Республикаһы':'Serbia', 'Сербия':'Serbia', 'Словакия':'Slovakia ', 'Төркиә':'Turkey', 'Украина':'Ukraine', 'Греция':'Greece', 'Ҡаҙағстан':'Kazakhstan', },
'be':{ 'Албанія':'Albania', 'Аўстрыя':'Austria', 'Азербайджан':'Azerbaijan', 'Башкартастан':'Bashkortostan', 'Беларусь':'Belarus', 'Балгарыя':'Bulgaria', 'Арменія':'Armenia', 'Боснія і Герцагавіна':'Bosnia and Herzegovina', 'Эрзя':'Erzia', 'Эсперанта':'Esperanto', 'Эстонія':'Estonia', 'Грузія':'Georgia', 'Чэхія':'Czechia', 'Харватыя':'Croatia', 'Рэспубліка Косава':'Kosovo', 'Крымскія татары':'Crimean Tatars', 'Літва':'Lithuania', 'Латвія':'Latvia', 'Венгрыя':'Hungary', 'Македонія':'Macedonia', 'Малдова':'Moldova', 'Польшча':'Poland', 'Расія':'Russia', 'Румынія':'Romania', 'Рэспубліка Сербская':'Serbia', 'Сербія':'Serbia', 'Славакія':'Slovakia ', 'Турцыя':'Turkey', 'Украіна':'Ukraine', 'Грэцыя':'Greece', 'Казахстан':'Kazakhstan', },
'be-tarask':{ 'Альбанія':'Albania', 'Аўстрыя':'Austria', 'Азэрбайджан':'Azerbaijan', 'Башкартастан':'Bashkortostan', 'Беларусь':'Belarus', 'Баўгарыя':'Bulgaria', 'Армэнія':'Armenia', 'Босьнія і Герцагавіна':'Bosnia and Herzegovina', 'Эрзя':'Erzia', 'Эспэранта':'Esperanto', 'Эстонія':'Estonia', 'Грузія':'Georgia', 'Чэхія':'Czechia', 'Харватыя':'Croatia', 'Косава':'Kosovo', 'Крымскія татары':'Crimean Tatars', 'Летува':'Lithuania', 'Латвія':'Latvia', 'Вугоршчына':'Hungary', 'Македонія':'Macedonia', 'Малдова':'Moldova', 'Польшча':'Poland', 'Расея':'Russia', 'Румынія':'Romania', 'Рэспубліка Сэрбская':'Serbia', 'Сэрбія':'Serbia', 'Славаччына':'Slovakia ', 'Турэччына':'Turkey', 'Украіна':'Ukraine', 'Грэцыя':'Greece', 'Казахстан':'Kazakhstan', },
'bg':{ 'Албания':'Albania', 'Австрия':'Austria', 'Азербайджан':'Azerbaijan', 'Башкортостан':'Bashkortostan', 'Беларус':'Belarus', 'България':'Bulgaria', 'Армения':'Armenia', 'Босна и Херцеговина':'Bosnia and Herzegovina', 'Эрзя':'Erzia', 'Есперанто':'Esperanto', 'Естония':'Estonia', 'Грузия':'Georgia', 'Чехия':'Czechia', 'Хърватия':'Croatia', 'Косово':'Kosovo', 'Кримски татари':'Crimean Tatars', 'Литва':'Lithuania', 'Латвия':'Latvia', 'Унгария':'Hungary', 'Македония':'Macedonia', 'Молдова':'Moldova', 'Полша':'Poland', 'Русия':'Russia', 'Румъния':'Romania', 'Република Сръбска':'Serbia', 'Сърбия':'Serbia', 'Словакия':'Slovakia ', 'Турция':'Turkey', 'Украйна':'Ukraine', 'Гърция':'Greece', 'Казахстан':'Kazakhstan', },
'de':{ 'Albanien':'Albania', 'Österreich':'Austria', 'Aserbaidschan':'Azerbaijan', 'Baschkortostan':'Bashkortostan', 'Weißrussland':'Belarus', 'Bulgarien':'Bulgaria', 'Armenien':'Armenia', 'Bosnien und Herzegowina':'Bosnia and Herzegovina', 'Ersja':'Erzia', 'Esperanto':'Esperanto', 'Estland':'Estonia', 'Georgien':'Georgia', 'Tschechien':'Czechia', 'Kroatien':'Croatia', 'Kosovo':'Kosovo', 'Krimtataren':'Crimean Tatars', 'Litauen':'Lithuania', 'Lettland':'Latvia', 'Ungarn':'Hungary', 'Mazedonien':'Macedonia', 'Moldawien':'Moldova', 'Polen':'Poland', 'Russland':'Russia', 'Rumänien':'Romania', 'Republika Srpska':'Serbia', 'Serbien':'Serbia', 'Slowakei':'Slovakia ', 'Türkei':'Turkey', 'Ukraine':'Ukraine', 'Griechenland':'Greece', 'Kasachstan':'Kazakhstan', },
'crh':{ 'Arnavutlıq':'Albania', 'Avstriya':'Austria', 'Azerbaycan':'Azerbaijan', 'Başqırtistan':'Bashkortostan', 'Belarus':'Belarus', 'Bulğaristan':'Bulgaria', 'Ermenistan':'Armenia', 'Bosna ve Hersek':'Bosnia and Herzegovina', 'Esperanto':'Esperanto', 'Estoniya':'Estonia', 'Gürcistan':'Georgia', 'Çehiya':'Czechia', 'Hırvatistan':'Croatia', 'Kosovo':'Kosovo', 'Qırımtatarlar':'Crimean Tatars', 'Litvaniya':'Lithuania', 'Latviya':'Latvia', 'Macaristan':'Hungary', 'Makedoniya':'Macedonia', 'Moldova':'Moldova', 'Lehistan':'Poland', 'Rusiye':'Russia', 'Romaniya':'Romania', 'Sırb Cumhuriyeti':'Serbia', 'Sırbistan':'Serbia', 'Slovakiya':'Slovakia ', 'Türkiye':'Turkey', 'Ukraina':'Ukraine', 'Yunanistan':'Greece', 'Qazahistan':'Kazakhstan', },
'el':{ 'Αλβανία':'Albania', 'Αυστρία':'Austria', 'Αζερμπαϊτζάν':'Azerbaijan', 'Μπασκορτοστάν':'Bashkortostan', 'Λευκορωσία':'Belarus', 'Βουλγαρία':'Bulgaria', 'Αρμενία':'Armenia', 'Βοσνία και Ερζεγοβίνη':'Bosnia and Herzegovina', 'Έρζυα':'Erzia', 'Εσπεράντο':'Esperanto', 'Εσθονία':'Estonia', 'Γεωργία':'Georgia', 'Τσεχία':'Czechia', 'Κροατία':'Croatia', 'Κόσοβο':'Kosovo', 'Τατάροι Κριμαίας':'Crimean Tatars', 'Λιθουανία':'Lithuania', 'Λετονία':'Latvia', 'Ουγγαρία':'Hungary', 'πΓΔΜ':'Macedonia', 'Μολδαβία':'Moldova', 'Πολωνία':'Poland', 'Ρωσία':'Russia', 'Ρουμανία':'Romania', 'Σερβική Δημοκρατία':'Serbia', 'Σερβία':'Serbia', 'Σλοβακία':'Slovakia ', 'Τουρκία':'Turkey', 'Ουκρανία':'Ukraine', 'Ελλάδα':'Greece', 'Καζακστάν':'Kazakhstan', },
'myv':{ 'Албания':'Albania', 'Австрия':'Austria', 'Азербайджан':'Azerbaijan', 'Башкирия':'Bashkortostan', 'Белорузия':'Belarus', 'Болгария':'Bulgaria', 'Армения':'Armenia', 'Босния ды Герцеговина':'Bosnia and Herzegovina', 'Эрзя':'Erzia', 'Эсперанто':'Esperanto', 'Эстэнь':'Estonia', 'Грузия':'Georgia', 'Чехия':'Czechia', 'Хорватия':'Croatia', 'Литва':'Lithuania', 'Латвия':'Latvia', 'Мадьяронь':'Hungary', 'Македония':'Macedonia', 'Молдавия':'Moldova', 'Польша':'Poland', 'Россия':'Russia', 'Румыния':'Romania', 'Сербань Республикась':'Serbia', 'Сербия':'Serbia', 'Словакия':'Slovakia ', 'Турция':'Turkey', 'Украина':'Ukraine', 'Греция':'Greece', 'Казахстан':'Kazakhstan', },
'eo':{ 'Albanio':'Albania', 'Aŭstrio':'Austria', 'Azerbajĝano':'Azerbaijan', 'Baŝkirio':'Bashkortostan', 'Belorusio':'Belarus', 'Bulgario':'Bulgaria', 'Armenio':'Armenia', 'Bosnio kaj Hercegovino':'Bosnia and Herzegovina', 'Erzja':'Erzia', 'Esperanto':'Esperanto', 'Estonio':'Estonia', 'Kartvelio':'Georgia', 'Ĉeĥio':'Czechia', 'Kroatio':'Croatia', 'Kosovo':'Kosovo', 'Krime-tataroj':'Crimean Tatars', 'Litovio':'Lithuania', 'Latvio':'Latvia', 'Hungario':'Hungary', 'Makedonio':'Macedonia', 'Moldava':'Moldova', 'Pollando':'Poland', 'Rusio':'Russia', 'Rumanio':'Romania', 'Serba Respubliko':'Serbia', 'Serbio':'Serbia', 'Slovakio':'Slovakia ', 'Turkio':'Turkey', 'Ukrainio':'Ukraine', 'Grekio':'Greece', 'Kazaĥio':'Kazakhstan', },
'hy':{ 'Ալբանիա':'Albania', 'Ավստրիա':'Austria', 'Ադրբեջանական Հանրապետություն':'Azerbaijan', 'Բաշկորտոստան':'Bashkortostan', 'Բելառուս':'Belarus', 'Բուլղարիա':'Bulgaria', 'Հայաստան':'Armenia', 'Բոսնիա և Հերցեգովինա':'Bosnia and Herzegovina', 'Էսպերանտո':'Esperanto', 'Էստոնիա':'Estonia', 'Վրաստան':'Georgia', 'Չեխիա':'Czechia', 'Խորվաթիա':'Croatia', 'Կոսովո':'Kosovo', 'Ղրիմի թաթարներ':'Crimean Tatars', 'Լիտվա':'Lithuania', 'Լատվիա':'Latvia', 'Հունգարիա':'Hungary', 'Մակեդոնիայի Հանրապետություն':'Macedonia', 'Մոլդովա':'Moldova', 'Լեհաստան':'Poland', 'Ռուսաստան':'Russia', 'Ռումինիա':'Romania', 'Սերբական Հանրապետություն':'Serbia', 'Սերբիա':'Serbia', 'Սլովակիա':'Slovakia ', 'Թուրքիա':'Turkey', 'Ուկրաինա':'Ukraine', 'Հունաստան':'Greece', 'Ղազախստան':'Kazakhstan', },
'ka':{ 'ალბანეთი':'Albania', 'ავსტრია':'Austria', 'აზერბაიჯანი':'Azerbaijan', 'ბაშკირეთი':'Bashkortostan', 'ბელარუსი':'Belarus', 'ბულგარეთი':'Bulgaria', 'სომხეთი':'Armenia', 'ბოსნია და ჰერცეგოვინა':'Bosnia and Herzegovina', 'ესპერანტო':'Esperanto', 'ესტონეთი':'Estonia', 'საქართველო':'Georgia', 'ჩეხეთი':'Czechia', 'ხორვატია':'Croatia', 'კოსოვო':'Kosovo', 'ყირიმელი თათრები':'Crimean Tatars', 'ლიტვა':'Lithuania', 'ლატვია':'Latvia', 'უნგრეთი':'Hungary', 'მაკედონია':'Macedonia', 'მოლდოვა':'Moldova', 'პოლონეთი':'Poland', 'რუსეთი':'Russia', 'რუმინეთი':'Romania', 'სერბთა რესპუბლიკა':'Serbia', 'სერბეთი':'Serbia', 'სლოვაკეთი':'Slovakia ', 'თურქეთი':'Turkey', 'უკრაინა':'Ukraine', 'საბერძნეთი':'Greece', 'ყაზახეთი':'Kazakhstan', },
'lv':{ 'Albānija':'Albania', 'Austrija':'Austria', 'Azerbaidžāna':'Azerbaijan', 'Baškortostāna':'Bashkortostan', 'Baltkrievija':'Belarus', 'Bulgārija':'Bulgaria', 'Armēnija':'Armenia', 'Bosnija un Hercegovina':'Bosnia and Herzegovina', 'Erzju':'Erzia', 'Esperanto':'Esperanto', 'Igaunija':'Estonia', 'Gruzija':'Georgia', 'Čehija':'Czechia', 'Horvātija':'Croatia', 'Kosova':'Kosovo', 'Krimas tatāri':'Crimean Tatars', 'Lietuva':'Lithuania', 'Latvija':'Latvia', 'Ungārija':'Hungary', 'Maķedonija':'Macedonia', 'Moldova':'Moldova', 'Polija':'Poland', 'Krievija':'Russia', 'Rumānija':'Romania', 'Serbu Republika':'Serbia', 'Serbija':'Serbia', 'Slovākija':'Slovakia ', 'Turcija':'Turkey', 'Ukraina':'Ukraine', 'Grieķija':'Greece', 'Kazahstāna':'Kazakhstan', },
'lt':{ 'Albanija':'Albania', 'Austrija':'Austria', 'Azerbaidžanas':'Azerbaijan', 'Baškirija':'Bashkortostan', 'Baltarusija':'Belarus', 'Bulgarija':'Bulgaria', 'Armėnija':'Armenia', 'Bosnija ir Hercegovina':'Bosnia and Herzegovina', 'Erzių':'Erzia', 'Esperanto':'Esperanto', 'Estija':'Estonia', 'Gruzija':'Georgia', 'Čekija':'Czechia', 'Kroatija':'Croatia', 'Kosovas':'Kosovo', 'Krymo totoriai':'Crimean Tatars', 'Lietuva':'Lithuania', 'Latvija':'Latvia', 'Vengrija':'Hungary', 'Makedonija':'Macedonia', 'Moldavija':'Moldova', 'Lenkija':'Poland', 'Rusija':'Russia', 'Rumunija':'Romania', 'Serbų respublika':'Serbia', 'Serbija':'Serbia', 'Slovakija':'Slovakia ', 'Turkija':'Turkey', 'Ukraina':'Ukraine', 'Graikija':'Greece', 'Kazachstanas':'Kazakhstan', },
'mk':{ 'Албанија':'Albania', 'Австрија':'Austria', 'Азербејџан':'Azerbaijan', 'Bashkortostani':'Bashkortostan', 'Белорусија':'Belarus', 'Бугарија':'Bulgaria', 'Ерменија':'Armenia', 'Босна и Херцеговина':'Bosnia and Herzegovina', 'Ерзја':'Erzia', 'Есперанто':'Esperanto', 'Естонија':'Estonia', 'Грузија':'Georgia', 'Чешка':'Czechia', 'Хрватска':'Croatia', 'Република Косово':'Kosovo', 'Кримски Татари':'Crimean Tatars', 'Литванија':'Lithuania', 'Латвија':'Latvia', 'Унгарија':'Hungary', 'Македонија':'Macedonia', 'Молдавија':'Moldova', 'Полска':'Poland', 'Русија':'Russia', 'Романија':'Romania', 'Република Српска':'Serbia', 'Србија':'Serbia', 'Словачка':'Slovakia ', 'Турција':'Turkey', 'Украина':'Ukraine', 'Грција':'Greece', 'Казахстан':'Kazakhstan', },
'ro':{ 'Albania':'Albania', 'Austria':'Austria', 'Azerbaidjan':'Azerbaijan', 'Bașchiria':'Bashkortostan', 'Belarus':'Belarus', 'Bulgaria':'Bulgaria', 'Armenia':'Armenia', 'Bosnia și Herțegovina':'Bosnia and Herzegovina', 'Esperanto':'Esperanto', 'Estonia':'Estonia', 'Georgia':'Georgia', 'Cehia':'Czechia', 'Croația':'Croatia', 'Kosovo':'Kosovo', 'Tătarii crimeeni':'Crimean Tatars', 'Lituania':'Lithuania', 'Letonia':'Latvia', 'Ungaria':'Hungary', 'Macedonia':'Macedonia', 'Moldova':'Moldova', 'Polonia':'Poland', 'Rusia':'Russia', 'România':'Romania', 'Republika Srpska':'Serbia', 'Serbia':'Serbia', 'Slovacia':'Slovakia ', 'Turcia':'Turkey', 'Ucraina':'Ukraine', 'Grecia':'Greece', 'Kazahstan':'Kazakhstan', },
'ru':{ 'Албания':'Albania', 'Австрия':'Austria', 'Азербайджан':'Azerbaijan', 'Башкортостан':'Bashkortostan', 'Белоруссия':'Belarus', 'Болгария':'Bulgaria', 'Армения':'Armenia', 'Босния и Герцеговина':'Bosnia and Herzegovina', 'Эрзя':'Erzia', 'Эсперанто':'Esperanto', 'Эстония':'Estonia', 'Грузия':'Georgia', 'Чехия':'Czechia', 'Хорватия':'Croatia', 'Косово':'Kosovo', 'Крымские татары':'Crimean Tatars', 'Литва':'Lithuania', 'Латвия':'Latvia', 'Венгрия':'Hungary', 'Македония':'Macedonia', 'Молдавия':'Moldova', 'Польша':'Poland', 'Россия':'Russia', 'Румыния':'Romania', 'Республика Сербская':'Serbia', 'Сербия':'Serbia', 'Словакия':'Slovakia ', 'Турция':'Turkey', 'Украина':'Ukraine', 'Греция':'Greece', 'Казахстан':'Kazakhstan', },
'sq':{ 'Shqipëria':'Albania', 'Austria':'Austria', 'Azerbajxhani':'Azerbaijan', 'Bashkortostani':'Bashkortostan', 'Bjellorusia':'Belarus', 'Bullgaria':'Bulgaria', 'Armenia':'Armenia', 'Bosnja dhe Hercegovina':'Bosnia and Herzegovina', 'Gjuha esperanto':'Esperanto', 'Estonia':'Estonia', 'Gjeorgjia':'Georgia', 'Republika Çeke':'Czechia', 'Kroacia':'Croatia', 'Kosova':'Kosovo', 'Lituania':'Lithuania', 'Letonia':'Latvia', 'Hungaria':'Hungary', 'Maqedonisë':'Macedonia', 'Moldavia':'Moldova', 'Polonia':'Poland', 'Rusia':'Russia', 'Rumania':'Romania', 'Serbia':'Serbia', 'Sllovakia':'Slovakia ', 'Turqia':'Turkey', 'Ukraina':'Ukraine', 'Greqia':'Greece', 'Kazakistani':'Kazakhstan', },
'sr':{ 'Албанија':'Albania', 'Аустрија':'Austria', 'Азербејџан':'Azerbaijan', 'Башкортостан':'Bashkortostan', 'Белорусија':'Belarus', 'Бугарска':'Bulgaria', 'Јерменија':'Armenia', 'Босна и Херцеговина':'Bosnia and Herzegovina', 'Ерзја':'Erzia', 'Есперанто':'Esperanto', 'Естонија':'Estonia', 'Грузија':'Georgia', 'Чешка':'Czechia', 'Хрватска':'Croatia', 'Република Косово':'Kosovo', 'Кримски Татари':'Crimean Tatars', 'Литванија':'Lithuania', 'Летонија':'Latvia', 'Мађарска':'Hungary', 'Република Македонија':'Macedonia', 'Молдавија':'Moldova', 'Пољска':'Poland', 'Русија':'Russia', 'Румунија':'Romania', 'Република Српска':'Serbia', 'Србија':'Serbia', 'Словачка':'Slovakia ', 'Турска':'Turkey', 'Украјина':'Ukraine', 'Грчка':'Greece', 'Казахстан':'Kazakhstan', },
'tt':{ 'Албания':'Albania', 'Австрия':'Austria', 'Азәрбайҗан':'Azerbaijan', 'Башкортстан':'Bashkortostan', 'Беларусия':'Belarus', 'Болгария':'Bulgaria', 'Әрмәнстан':'Armenia', 'Босния һәм Герцеговина':'Bosnia and Herzegovina', 'Ирзә':'Erzia', 'Эсперанто':'Esperanto', 'Эстония':'Estonia', 'Гөрҗистан':'Georgia', 'Чехия':'Czechia', 'Хорватия':'Croatia', 'Косово Җөмһүрияте':'Kosovo', 'Кырым татарлары':'Crimean Tatars', 'Литва':'Lithuania', 'Latviä':'Latvia', 'Маҗарстан':'Hungary', 'Македония':'Macedonia', 'Молдова':'Moldova', 'Польша':'Poland', 'Русия':'Russia', 'Румыния':'Romania', 'Сербия':'Serbia', 'Словакия':'Slovakia ', 'Төркия':'Turkey', 'Украина':'Ukraine', 'Греция':'Greece', 'Казакъстан':'Kazakhstan', },
'tr':{ 'Arnavutluk':'Albania', 'Avusturya':'Austria', 'Azerbaycan':'Azerbaijan', 'Başkurdistan':'Bashkortostan', 'Beyaz Rusya':'Belarus', 'Bulgaristan':'Bulgaria', 'Ermenistan':'Armenia', 'Bosna-Hersek':'Bosnia and Herzegovina', 'Erzya':'Erzia', 'Esperanto':'Esperanto', 'Estonya':'Estonia', 'Gürcistan':'Georgia', 'Çek Cumhuriyeti':'Czechia', 'Hırvatistan':'Croatia', 'Kosova':'Kosovo', 'Kırım Tatarları':'Crimean Tatars', 'Litvanya':'Lithuania', 'Letonya':'Latvia', 'Macaristan':'Hungary', 'Makedonya':'Macedonia', 'Moldova':'Moldova', 'Polonya':'Poland', 'Rusya':'Russia', 'Romanya':'Romania', 'Sırp Cumhuriyeti':'Serbia', 'Sırbistan':'Serbia', 'Slovakya':'Slovakia ', 'Türkiye':'Turkey', 'Ukrayna':'Ukraine', 'Yunanistan':'Greece', 'Kazakistan':'Kazakhstan', },
'uk':{ 'Албанія':'Albania', 'Австрія':'Austria', 'Азербайджан':'Azerbaijan', 'Башкортостан':'Bashkortostan', 'Білорусь':'Belarus', 'Болгарія':'Bulgaria', 'Вірменія':'Armenia', 'Боснія і Герцеговина':'Bosnia and Herzegovina', 'Ерзя':'Erzia', 'Есперанто':'Esperanto', 'Естонія':'Estonia', 'Грузія':'Georgia', 'Чехія':'Czechia', 'Хорватія':'Croatia', 'Косово':'Kosovo', 'Кримські татари':'Crimean Tatars', 'Литва':'Lithuania', 'Латвія':'Latvia', 'Угорщина':'Hungary', 'Македонія':'Macedonia', 'Молдова':'Moldova', 'Польща':'Poland', 'Росія':'Russia', 'Румунія':'Romania', 'Республіка Сербська':'Serbia', 'Сербія':'Serbia', 'Словаччина':'Slovakia ', 'Туреччина':'Turkey', 'Україна':'Ukraine', 'Греція':'Greece', 'Казахстан':'Kazakhstan', },
'hu':{ 'Albánia':'Albania', 'Ausztria':'Austria', 'Azerbajdzsán':'Azerbaijan', 'Baskirföld':'Bashkortostan', 'Belorusz':'Belarus', 'Bulgária':'Bulgaria', 'Örményország':'Armenia', 'Bosznia és Hercegovina':'Bosnia and Herzegovina', 'Eszperantó':'Esperanto', 'Észtország':'Estonia', 'Grúzia':'Georgia', 'Csehország':'Czechia', 'Horvátország':'Croatia', 'Koszovo':'Kosovo', 'Krími tatárok':'Crimean Tatars', 'Litvánia':'Lithuania', 'Lettország':'Latvia', 'Magyarország':'Hungary', 'Macedónia':'Macedonia', 'Moldávia':'Moldova', 'Lengyelország':'Poland', 'Oroszország':'Russia', 'Románia':'Romania', 'Boszniai Szerb Köztársaság':'Serbia', 'Szerbia':'Serbia', 'Szlovákia':'Slovakia ', 'Törökország':'Turkey', 'Ukrajna':'Ukraine', 'Görögország':'Greece', 'Kazahsztán':'Kazakhstan', },
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
             'mk':0, 'ro':0, 'ru':0, 'sq':0, 'sr':0, 'tt':0, 'tr':0, 'uk':0, 'hu':0}
    countryp = { 'pl':'kraj', 'az':'ölkə', 'ba':'ил', 'be':'краіна', 'Be-tarask':'краіна', 'bg':'държава', 'de':'land', 'crh':'memleket', 'el':'country', \
                 'myv':'мастор', 'eo':'country', 'ka':'ქვეყანა', 'lv':'valsts', 'lt':'šalis', 'mk':'земја', 'ro':'țară', 'ru':'страна', 'sq':'country', \
                 'sr':'држава', 'tt':'ил', 'tr':'ülke', 'uk':'країна' }
    topicp = {'pl':'parametr', 'az':'qadınlar', 'ba':'тема', 'be':'тэма', 'Be-tarask':'тэма', 'bg':'тема', 'de':'thema', 'crh':'mevzu', 'el':'topic', \
             'myv':'тема', 'eo':'topic', 'ka':'თემა', 'lv':'tēma', 'lt':'tema', 'mk':'тема', 'ro':'subiect', 'ru':'тема', 'sq':'topic', 'sr':'тема', \
             'tt':'тема', 'tr':'konu', 'uk':'тема'}
    womenp = {'pl':'kobiety', 'az':'qadınlar', 'ba':'Ҡатын-ҡыҙҙар', 'be':'Жанчыны', 'Be-tarask':'жанчыны', 'bg':'жени', 'de':'Frauen','el':'γυναίκες', \
              'ka':'ქალები', 'lv':'Sievietes','mk':'Жени', 'ro':'Femei', 'ru':'женщины', 'sq':'Gratë', 'sr':'Жене', 'tt':'Хатын-кызлар', 'tr':'Kadın', 'uk':'жінки', 'hu':'nők'}
    

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
            if aInfo['creator'] not in self.authors.keys():
                self.authors[aInfo['creator']] = 1
            else:
                self.authors[aInfo['creator']] += 1

        self.generateArticleList(self.springList,self.getOption('outpage')+u'/Article list',header,footer)
        self.generateAuthorsPage(self.authors,self.getOption('outpage')+u'/Authors list',header,footer)
        self.generateWomenPage(self.authors,self.getOption('outpage')+u'/Articles about women',header,footer)

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
                if lang not in ('crh'):
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
            artParams['newarticle'] = self.newArticle(creationDate)

            if lang in CEEtemplates.keys() and talk.exists():
                TmplInfo = self.getTemplateInfo(talk, CEEtemplates[lang], lang)
                artParams['template'] = TmplInfo

            if not artParams['newarticle']:
                artParams['creator'], artParams['creationDate'] = self.getUpdater(art)


            #print artParams
        return(artParams)

    def getUpdater(self, art):
        #find author and update datetime of the biggest update within CEESpring

        return(art.getCreator())

    def newArticle(self,creationDate):
        #check if the article was created within CEE Spring
        SpringStart =  datetime.strptime("2017-03-21T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
        SpringEnd = datetime.strptime("2017-06-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
        return ( datetime.strptime(creationDate, "%Y-%m-%dT%H:%M:%SZ") > SpringStart )


    def getTemplateInfo(self,page,template,lang):
        param = {}
        #return dictionary with template params
        for t in page.templatesWithParams():
            title, params = t
            #print(title)
            #print(params)
            tt = re.sub(ur'\[\[.*?:(.*?)\]\]', r'\1', title.title())
            if self.getOption('test'):
                pywikibot.output(u'tml:%s = %s = %s' % (title,tt,template) )
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
                    #check article about women
                    if lang in self.topicp.keys() and name.lower().startswith(self.topicp[lang].lower()):
                        if self.getOption('test'):
                            pywikibot.output(u'topic:%s:%s' % (name,value))
                        if lang in self.womenp.keys() and value.lower().startswith(self.womenp[lang].lower()):
                            self.women[lang] += 1
                    #check article about country
                    if lang in self.countryp.keys() and name.lower().startswith(self.countryp[lang].lower()):
                        if self.getOption('test'):
                            pywikibot.output(u'country:%s:%s' % (name,value))
                        if lang in countryNames.keys() and value in (countryNames[lang].keys()):
                            countryEN = countryNames[lang][value]
                            if lang not in self.pagesCount.keys():
                                self.pagesCount[lang] = {}
                            if countryEN in self.pagesCount[lang].keys():
                                self.pagesCount[lang][countryEN] += 1
                            else:
                                self.pagesCount[lang][countryEN] = 1
                    print self.pagesCount
                print param
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

    def generateWomenPage(self, res, pagename, header, footer):
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
        updatedArticles = u'\n\n=== updated articles ==='

        itemcount = 0
        #go by language
        for l in res.keys():
            #print('[[:' + i + u':' + self.templatesList[i] +u'|' + i + u' wikipedia]]')
            if l in self.templatesList.keys():
                finalpage += u'\n== [[:' + l + u':Template:' + self.templatesList[l] +u'|' + l + u'.wikipedia]] =='
            else:
                finalpage += u'\n== ' + l + u'.wikipedia =='
            finalpage += u'\n=== new articles ==='
            for i in res[l]:
                itemcount += 1
                artLine = u'\n# [[:' + i['lang'] + u':' + i['title'] + u']] - user:' + i['creator'] + u' date:' + i['creationDate']
                if i['newarticle']:
                    #finalpage += u' (NEW)'
                    finalpage += artLine
                    pywikibot.output(u'# [[:' + i['lang'] + u':' + i['title'] + u']] - user:' + i['creator'] + u' date:' + i['creationDate'] + u' (NEW)')
                else:
                    #finalpage += u" '''(updated)'''"
                    updatedArticles += artLine
                    pywikibot.output(u'# [[:' + i['lang'] + u':' + i['title'] + u']] - user:' + i['creator'] + u' date:' + i['creationDate'] + u" '''(updated)'''")

                #if self.getOption('test'):
                #    pywikibot.output(u'\n# [[:' + i['lang'] + u':' + i['title'] + u']] - user:' + i['creator'] + u' date:' + i['creationDate'])

            finalpage += updatedArticles

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
