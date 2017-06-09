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
    header = u'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
    header += u'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pl" lang="pl" dir="ltr">\n'
    header += u'	<head>\n'
    header += u'		<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n'
    header += u'		<meta http-equiv="refresh" content="300">\n'
    header += u'		<title>Licznik artykułów pl.wikipedia - ostatnie 100 pozycji - tools.wikimedia.pl</title>\n'
    header += u'		<link rel="stylesheet" type="text/css" href="/~masti/modern.css" />\n'
    header += u'	</head>\n'
    header += u'<body>\n'
    header += u'\n'
    header += u'	<!-- heading -->\n'
    header += u'\n'
    header += u'	<div id="mw_header">\n'
    header += u'		<h1 id="firstHeading">Ostatnie nowe artykuły</h1>\n'
    header += u'	</div>\n'
    header += u'\n'
    header += u'	<div id="mw_main">\n'
    header += u'	<div id="mw_contentwrapper">\n'
    header += u'\n'
    header += u'	<!-- content -->\n'
    header += u'	<div id="mw_content">\n'
    header += u'\n'
    header += u'		<p>Strona przedstawia numerację ostatnio utworzonych 100 artykułów z głównej przestrzeni nazw.<br />\n'
    header += u'		<small>Rodzaj: <b>A</b> (artykuł), <b>R</b> (przekierowanie)</small><br />\n'
    header += u'		<small>Strona uaktualniana co 5 minut. Wyświetlanie od najnowszych</small><br />\n'
    header += u'		</p>\n'
    # add creation time
    header += u'		<p>Ostatnia aktualizacja: <b>' + strftime('%A %d %B %Y %X %Z').encode('UTF-8') + u'</b></p>\n'
    header += u'\n'
    #
    header += u'                <center>\n'
    header += u'		<table class="wikitable" style="width:85%">\n'
    header += u'			<tr>\n'
    header += u'				<th>Numer artykułu</th>\n'
    header += u'				<th>Data</th>\n'
    header += u'				<th>Czas</th>\n'
    header += u'				<th>Rodzaj</th>\n'
    header += u'				<th>Tytuł</th>\n'
    header += u'				<th>Cel</th>\n'
    header += u'			</tr>\n'
    return(header)

def footer():
    #generate html file footer
    footer = u'		</table>\n'
    footer += u'                </center> \n'
    footer += u'\n'
    footer += u'	</div><!-- mw_content -->\n'
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
    footer += u'</body></html>'
    return(footer)

def outputRow(logline):
    #creates one output row
    s = re.sub(u'\n',u'',logline)
    #print s
    try:
        anum,adtime,atype,atitle,atarget =  s.split(u';')
        adate, atime = adtime.split()
    except:
        return(None)
    # encode URLs for title and target
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
    page = pywikibot.Page(pywikibot.Site(), atitle)

    if page.exists():
        astyle = u''
        if page.isRedirectPage():
            astyle = u' style="color:#308050">'
            try:
                tpage = page.getRedirectTarget()
            except:
                tpage = None
            ttitle = tpage.title()
            targetshow = True
            if tpage.exists():
                if tpage.isRedirectPage():
                    tstyle = u' style="color:#308050">'
                else:
                    tstyle  = u''
            else:
                tstyle = u' style="color:#CC2200">'
        else:
            astyle = u' style="color:#CC2200">'
            if atype = u'R':
                tpage = pywikibot.Page(pywikibot.Site(), atarget)
                ttitle = tpage.title()
                if tpage.exists():
                    if tpage.isRedirectPage():
                        tstyle = u' style="color:#308050">'
                    else:
                        tstyle  = u''
                else:
                    tstyle = u' style="color:#CC2200">'

    urlatitle = urllib.quote((u'//pl.wikipedia.org/wiki/' + atitle).encode('UTF-8'))
    urlatarget = urllib.quote((u'//pl.wikipedia.org/wiki/' + atarget).encode('UTF-8'))


    result += u'\t\t\t\t<td><a href="'+ utitle + u'"' + atitle + u'</a></td>\n'

    if atype == u'R':
        if page.exists():
            result += u'\t\t\t\t<td><a href="'+ utitle + u'" style="color:#308050">' + atitle + u'</a></td>\n'
        else:
            result += u'\t\t\t\t<td><a href="'+ utitle + u'" style="color:#CC2200">' + atitle + u'</a></td>\n'
    else:
        if page.exists():
            result += u'\t\t\t\t<td><a href="'+ utitle + u'">' + atitle + u'</a></td>\n'
        else:
            result += u'\t\t\t\t<td><a href="'+ utitle + u'" style="color:#CC2200">' + atitle + u'</a></td>\n'
    if atarget == u'':
        result += u'\t\t\t\t<td></td>\n'
    elif atarget == u'BŁĄD PRZEKIEROWANIA':
        result += u'\t\t\t\t<td>BŁĄD PRZEKIEROWANIA</td>\n'
    else:
        redir = pywikibot.Page(pywikibot.Site(), atarget)
        utarget = urllib.quote((u'//pl.wikipedia.org/wiki/' + atarget).encode('UTF-8'))
        if redir.exists():
            result += u'\t\t\t\t<td><a href="'+ utarget + u'">' + atarget + u'</a></td>\n'
        else:
            result += u'\t\t\t\t<td><a href="'+ utarget + u'" style="color:#CC2200">' + atarget + u'</a></td>\n'
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
        r = outputRow(a)
        if r:
            result += outputRow(a)
    result += footer()
    file = codecs.open('masti/artykuly.html', 'w', 'utf-8')
    # printout log
    pywikibot.output(result)
    file.write(result)
    file.close()

if __name__ == '__main__':
    main()
