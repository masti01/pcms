#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import pywikibot
import codecs
import urllib

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
    
    for a in reversed(arts):
        result += outputRow(a)
    file = codecs.open('masti/artnosbody.html', 'w', 'utf-8')
    # printout log
    pywikibot.output(result)
    file.write(result)
    file.close()

if __name__ == '__main__':
    main()
