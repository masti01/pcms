#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import sys
import pywikibot
import codecs
import urllib
from datetime import datetime
from time import strftime

i18 = {
'pl' : {
    'head' : u'Licznik artykułów pl.wikipedia - ostatnie 100 pozycji - tools.wikimedia.pl',
    'heading' : u'Ostatnie nowe artykuły',
    'line1' : u'Strona przedstawia numerację ostatnio utworzonych 100 artykułów z głównej przestrzeni nazw.',
    'legend' : u'Rodzaj: <b>A</b> (artykuł), <b>R</b> (przekierowanie)',
    'lastupdate' : u'Ostatnia aktualizacja: ',
    'refresh' : u'Strona uaktualniana co 5 minut. Wyświetlanie od najnowszych.',
    'hnumber' : u'Numer artykułu',
    'htype' : u'Rodzaj',
    'hdate' : u'Data',
    'htime' : u'Czas',
    'htitle' : u'Tytuł',
    'htarget' : u'Cel' },
'tr' : {
    'head' : u'Article counter tr.wikipedia - last 100 articles - tools.wikimedia.pl',
    'heading' : u'Last new articles',
    'line1' : u"Sayfa, belirtilen dil sürümündeki son 100 makalenin makale ID'lerini gösterir",
    'legend' : u'Tür: <b>A</b> (madde), <b>R</b> (yönlendirme)',
    'lastupdate' : u'Son güncellenme: ',
    'refresh' : u'Sayfa 5 dakikada bir yenilenir. En yeni, en başta gösterilir.',
    'hnumber' : u'Madde no',
    'htype' : u'Tür',
    'hdate' : u'Tarih',
    'htime' : u'Saat',
    'htitle' : u'Başlık',
    'htarget' : u'Hedef' }
}


def header(lang):
    #generate html file header
    header = u'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
    header += u'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pl" lang="pl" dir="ltr">\n'
    header += u'	<head>\n'
    header += u'		<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n'
    header += u'		<meta http-equiv="refresh" content="300">\n'
    header += u'		<title>' + i18[lang]['head'] + u'</title>\n'
    header += u'		<link rel="stylesheet" type="text/css" href="/~masti/modern.css" />\n'
    header += u'	</head>\n'
    header += u'<body>\n'
    header += u'\n'
    header += u'	<!-- heading -->\n'
    header += u'\n'
    header += u'	<div id="mw_header">\n'
    header += u'		<h1 id="firstHeading">' + i18[lang]['heading'] + u'</h1>\n'
    header += u'	</div>\n'
    header += u'\n'
    header += u'	<div id="mw_main">\n'
    header += u'	<div id="mw_contentwrapper">\n'
    header += u'\n'
    header += u'	<!-- content -->\n'
    header += u'	<div id="mw_content">\n'
    header += u'\n'
    header += u'		<p>' + i18[lang]['line1'] + u'<br />\n'
    header += u'		<small>' + i18[lang]['legend'] + u'</small><br />\n'
    header += u'		<small>' + i18[lang]['refresh'] + u'</small><br />\n'
    header += u'		</p>\n'
    # add creation time
    header += u'		<p>' + i18[lang]['lastupdate'] + u'<b>' + strftime('%A %d %B %Y %X %Z').encode('UTF-8') + u'</b></p>\n'
    header += u'\n'
    #
    header += u'                <center>\n'
    header += u'		<table class="wikitable" style="width:85%">\n'
    header += u'			<tr>\n'
    header += u'				<th>' + i18[lang]['hnumber'] + u'</th>\n'
    header += u'				<th>' + i18[lang]['hdate'] + u'</th>\n'
    header += u'				<th>' + i18[lang]['htime'] + u'</th>\n'
    header += u'				<th>' + i18[lang]['htype'] + u'</th>\n'
    header += u'				<th>' + i18[lang]['htitle'] + u'</th>\n'
    header += u'				<th>' + i18[lang]['htarget'] + u'</th>\n'
    header += u'			</tr>\n'
    return(header)

def footer(lang):
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

def outputRow(logline,lang):
    #creates one output row
    s = re.sub(u'\n',u'',logline)
    #print s
    try:
        anum,adtime,atype,atitle,atarget =  s.split(u';')
        adate, atime = adtime.split()
    except:
        return(None)
    # encode URLs for title and target
    utitle = urllib.quote((u'//' + lang + u'.wikipedia.org/wiki/' + atitle).encode('UTF-8'))
    print utitle
    if atarget == u'':
        utarget = u''
    else:
        utarget = urllib.quote((u'//' + lang + u'.wikipedia.org/wiki/' + atarget).encode('UTF-8'))
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
                ttitle = tpage.title()
            except:
                tpage = None
                ttitle = u''
              
            if tpage: 
                if tpage.exists():
                    if tpage.isRedirectPage():
                        tstyle = u' style="color:#308050">'
                    else:
                        tstyle  = u''
                else:
                    tstyle = u' style="color:#CC2200">'
            else:
                tstyle  = u''
        else:
            astyle = u' style="color:#CC2200">'
            if atype == u'R':
                tpage = pywikibot.Page(pywikibot.Site(), atarget)
                ttitle = tpage.title()
                if tpage.exists():
                    if tpage.isRedirectPage():
                        tstyle = u' style="color:#308050">'
                    else:
                        tstyle  = u''
                else:
                    tstyle = u' style="color:#CC2200">'

    urlatitle = urllib.quote((u'//' + lang + u'.wikipedia.org/wiki/' + atitle).encode('UTF-8'))
    urlatarget = urllib.quote((u'//' + lang + u'.wikipedia.org/wiki/' + atarget).encode('UTF-8'))


    #result += u'\t\t\t\t<td><a href="'+ utitle + u'">' + atitle + u'</a></td>\n'

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
    elif atarget == u'REDIRECT ERROR':
        result += u'\t\t\t\t<td>REDIRECT ERROR</td>\n'
    else:
        redir = pywikibot.Page(pywikibot.Site(), atarget)
        utarget = urllib.quote((u'//' + lang + u'.wikipedia.org/wiki/' + atarget).encode('UTF-8'))
        if redir.exists():
            result += u'\t\t\t\t<td><a href="'+ utarget + u'">' + atarget + u'</a></td>\n'
        else:
            result += u'\t\t\t\t<td><a href="'+ utarget + u'" style="color:#CC2200">' + atarget + u'</a></td>\n'
    result += u'\t\t\t</tr>\n'

    #pywikibot.output(result)
    return(result)
    

def main(*args):
    for arg in sys.argv:
        if arg.startswith('-lang:'):
            lang = arg[6:]
    site = pywikibot.Site(lang,fam='wikipedia')

    artlist = []
    result = u''
    
    logfile = u'ircbot/artnos' + lang + u'.log'
    resultfile = u'masti/artykuly' + lang + u'.html'

    file = codecs.open(logfile, "r", "utf-8")
    artlist  = file.readlines()
    file.close()
    arts = artlist[-100:]

    #print artlist
    
    result = header(lang)
    for a in reversed(arts):
        r = outputRow(a,lang)
        if r:
            result += r
    result += footer(lang)
    file = codecs.open(resultfile, 'w', 'utf-8')
    # printout log
    pywikibot.output(result)
    file.write(result)
    file.close()

if __name__ == '__main__':
    main()
