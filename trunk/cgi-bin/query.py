#!/usr/bin/python

from sys import path,argv
#path.append("../")
import cgi
import cgitb
from time import time
startTime = time()

from searchengine import searcher

cgitb.enable()
debug = 0

form = cgi.FieldStorage()

if __name__ == "__main__":
    debug = 1
    debug = 0

def htmlHeader(text):
    print "Content-Type: text/plain"
    print                       # empty line
    print """<!DOCTYPE html PUBLIC
      "-//W3C//DTD XHTML 1.0 Transitional//EN"
      "DTD/xhtml1-transitional.dtd">"""

    print """
   <html xmlns = "http://www.w3.org/1999/xhtml" xml:lang="en"
      lang="en">
      <head><title>Result of %s</title></head>
      <body><table style = "border: 0">""" % text

    print "<head> <html>"

def tail():
    print "</html></head>"

def beginResult():
    print "<hr>"

def noResult():
    HtmlHeader()
    print """<H1>Empty Search</H1>please Input words and search again."""
    tail()

def contextHeader(text,rescount=100):
    t = time() - startTime
    timeStr = '%.5f' % t
    timeStr.rstrip('0')
    print 'Result <b>1-10</b>" of about <b>%d</b> for <b>%s</b>.(%s seconds)'    % (rescount, text, timeStr)


if "text" not in form and not debug:
    noResult()
    exit
else:
    s = []
    if debug: text = argv[1]
    else:
        text = form.getValue("text")
    s = searcher.searcher("/var/local/se/engine.db")
    htmlHeader(text)
    
    result = s.query(text)
    contextHeader(text)
    beginResult()
    
    if (result == []):
        noResult()
        exit
    else:
        for (score,url) in result:
            print '<a href="%s">%s</a><br>' % (cgi.escape(url),cgi.escape(url[0:50]))
            print '<br>'


