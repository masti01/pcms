#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import pywikibot
import codecs
import urllib
from datetime import datetime
from time import strftime

def header():
    #generate html file header
    header = u'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
    header += u'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pl" lang="pl" dir="ltr">'
    header += u'	<head>'
    header += u'		<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'
    header += u'		<meta http-equiv="refresh" content="300">'
    header += u'		<title>Licznik artykułów pl.wikipedia - ostatnie 100 pozycji - tools.wikimedia.pl</title>'
    header += u'		<link rel="stylesheet" type="text/css" href="/~masti/modern.css" />'
    header += u'	</head>'
    header += u'<body>'
    header += u''
    header += u'	<!-- heading -->'
    header += u''
    header += u'	<div id="mw_header">'
    header += u'		<h1 id="firstHeading">Ostatnie nowe artykuły</h1>'
    header += u'	</div>'
    header += u''
    header += u'	<div id="mw_main">'
    header += u'	<div id="mw_contentwrapper">'
    header += u''
    header += u'	<!-- content -->'
    header += u'	<div id="mw_content">		'
    header += u''
    header += u'		<p>Strona przedstawia numerację ostatnio utworzonych 100 artykułów z głównej przestrzeni nazw.<br />'
    header += u'		Rodzaj: A (artykuł), R (przekierowanie)<br />	'
    header += u'		<small>Strona uaktualniana co 5 minut</small><br />	'
    header += u'		<small>Wyświetlanie od najnowszych</small>'
    # add creation time
    header += u'		<p>Ostatnia aktualizacja: <b>' + strftime('%A %d %B %Y %X %Z').encode('UTF-8') + u'</b></p>\n'
    header += u'\n'
    #
    header += u'		</p>'
    header += u'                <center>'
    header += u'		<table class="wikitable" style="width:85%">'
    header += u'			<tr>'
    header += u'				<th>Numer artykułu</th>'
    header += u'				<th>Data</th>'
    header += u'				<th>Czas</th>'
    header += u'				<th>Rodzaj</th>'
    header += u'				<th>Tytuł</th>'
    header += u'				<th>Cel</th>'
    header += u'			</tr>'


def footer():
    #generate html file footer
    footer = u'		</table>'
    footer += u'                </center> '
    footer += u''
    footer += u'	</div><!-- mw_content -->'
    footer += u'	</div><!-- mw_contentwrapper -->'
    footer += u''
    footer += u'	</div><!-- main -->'
    footer += u''
    footer += u'	<div class="mw_clear"></div>'
    footer += u''
    footer += u'	<!-- personal portlet -->'
    footer += u'	<div class="portlet" id="p-personal">'
    footer += u'		<div class="pBody">'
    footer += u'			<ul>'
    footer += u'				<li><a href="http://pl.wikipedia.org">wiki</a></li>'
    footer += u'				<li><a href="/">tools</a></li>'
    footer += u'				<li><a href="/~masti/">masti</a></li>'
    footer += u'			</ul>'
    footer += u'		</div>'
    footer += u'		</div>'
    footer += u'<div class="stopka">layout by <a href="../~beau/">Beau</a></div>'
    footer += u'</body></html>'
    return(footer)

def outputRow(logline):
    #creates one output row
    s = re.sub(u'\n',u'',logline)
    #print s
    anum,adtime,atype,atitle,atarget =  s.split(u';')
    adate, atime = adtime.split()
    # ecode URLs for title and target
    utitle = urllib.quote((u'//pl.wikipedia.org/wiki/' + atitle).encode('UTF-8'))
    if atarget == u'':
        utarget = u''
    else:
        utarget = urllib.quote((u'//pl.wikipedia.org/wiki/' + atarget).encode('UTF-8'))
    # create output
    result = u'\t\t\t<tr>\n'
    result += u'\t\t\t\t<td>' + anum +'</td>\n'
    result += u'\t\t\t\t<td>' + adate +'</td>\n'
    result += u'\t\t\t\t<td>' + atime +'</td>\n'
    result += u'\t\t\t\t<td>' + atype +'</td>\n'
    result += u'\t\t\t\t<td><a href="'+ utitle + u'">' + atitle + u'</a></td>\n'
    if atarget == u'':
        result += u'\t\t\t\t<td></td>\n'
    else:
        utarget = urllib.quote((u'//pl.wikipedia.org/wiki/' + atarget).encode('UTF-8'))
        result += u'\t\t\t\t<td><a href="'+ utarget + u'">' + atarget + u'</a></td>\n'
    result += u'\t\t\t</tr>\n'

    #pywikibot.output(result)
    return(result)
    

def main(*args):

    artlist = []
    result = u''
    
    file = codecs.open("ircbot/artnos.log", "r", "utf-8")
    artlist  = file.readlines()
    file.close()
    arts = artlist[-100:]

    #print artlist
    
    result = header()
    for a in reversed(arts):
        result += outputRow(a)
    result += footer()
    file = codecs.open('~/public_html/articles.html', 'w', 'utf-8')
    # printout log
    pywikibot.output(result)
    file.write(result)
    file.close()

if __name__ == '__main__':
    main()
