#!/usr/bin/python

debug = False

from sys import path,argv
#path.append("../")
import cgi
import cgitb
from time import time
startTime = time()

from searchengine import searcher

cgitb.enable()

form = cgi.FieldStorage()

if (debug): cgi.print_form(form)

def htmlHeader(text = ''):
    decl = "Content-Type: text/html\n"
    
    # decl += """<!DOCTYPE html PUBLIC
    #  "-//W3C//DTD XHTML 1.0 Transitional//EN"
    #  "DTD/xhtml1-transitional.dtd">"""
    if text == "":
        Title = "Search"
    else:
        Title = "Result of %s" % text
   
    head =  """
   <html xmlns = "http://www.w3.org/1999/xhtml" xml:lang="en"
      lang="en">
      <head><title>%s</title></head>
      <body><table style = "border: 0">""" % Title

    search= """
        <form enctype="multipart/form-data"
          method=post
          action="search">
      <input id=text maxLength=256 name=q value="" size=50><br>
      <input type=submit value="Search">
    </form>"""
    
    return decl + head + search

def tail():
    return "</html></head>"

def beginResult():
    return "<hr>"
def noResult():
    str = htmlHeader()
    str += beginResult()
    return str + """<H1>Empty Search</H1>please Input words and search again.""" + tail()

def contextHeader(text,rescount=100):
    t = time() - startTime
    timeStr = '%.5f' % t
    timeStr.rstrip('0')
    return 'Result <b>1-10</b>" of about <b>%d</b> for <b>%s</b>.(%s seconds)'    % (rescount, cgi.escape(text), timeStr)

def main():
    if not debug and not form.has_key('q'):
        # TODO Maybe return an query html page is better?
        print noResult()
        exit
    else:
        s = []
#        if debug:
#            pass
            #text = argv[1]
#        else:
        text = form["q"].value
            
        if debug: print "text is :",text
        s = searcher.searcher("/var/local/se/engine.db")
        page = htmlHeader(text)
        
        result = s.query(text)
        page += contextHeader(text)
        page += beginResult()
        
        if (result == []):
            print noResult()
            exit
        else:
            for (score,url) in result:
                page += '<a href="%s">%s</a><br>' % (cgi.escape(url),cgi.escape(url[0:50]))
                page += '<br>'
            print page

main()
